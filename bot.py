import atproto
import os
import time
import lmstudio as lms
import re
import datetime

def can_be_fact_checked(model, text):
    # can be used to determine if a trending post is checkable, or if the bot should check the "reply" where it's mentioned, or the root post
    # but LLMs are stupid, this doesn't work very well
    return True
    query = f"\"{text}\". Did I claim anything? Ignore whether I am correct or not, just say YES if I was claiming any facts, and NO otherwise"
    response = model.respond(query).content
    print(response)
    return "yes" in response.split(" ")[0].lower()


def fact_check(model, text):
    # ask LLM whether some post is accurate, and why
    query = f"\"{text}\". was this accurate? explain why in a couple of sentences"
    response = model.respond(query).content
    # summarize long answers
    if len(response) >= 585:
        print(f"\"{response}\" Too long ({len(response)}), summarizing...")
        response = response.replace("\"", "'").replace("“", "'").replace("”", "'")
        query = f"\"{response}\". can you summarize this?"
        response = model.respond(query).content
    print(response)
    return response + " *beep boop*"


def post_fact_check(model, client, post_text, reply_ref):
    # fact check something, and post response
    post_text = post_text.replace("\"", "'").replace("“", "'").replace("”", "'")
    post_text = re.sub(r'\B@[\w.]+', "", post_text)
    post_text = post_text.strip()
    print(f'Checking \"{post_text}\"')
    if can_be_fact_checked(model, post_text):
        response = fact_check(model, post_text)

        # split responses into 300 character posts
        post_text = ""
        for word in response.split(" "):
            if len(post_text)+len(word) > 295:
                print("Posting a split answer...")
                client.send_post(
                    text=post_text+"...",
                    reply_to=reply_ref,
                )
                post_text = ""
            post_text = post_text + word + " "

        print("Posting final answer.")
        client.send_post(
            text=post_text,
            reply_to=reply_ref,
        )
        return True
    print("Can't be fact checked")
    return False


def main():
    usr_name = os.environ.get("ATP_AUTH_HANDLE")
    usr_pw = os.environ.get("ATP_AUTH_PASSWORD")
    client = atproto.Client()
    profile = client.login(usr_name, usr_pw)

    with lms.Client() as lmc_client:
        model = lmc_client.llm.model("mistral-nemo-instruct-2407")
        print("Loading...")
        model.respond("Tell me the word \"ok\"")
        print("Done")

        # run in a loop
        latest_notif_found = client.get_current_time()
        while True:
            # save the time in UTC when we fetch notifications
            last_seen_at_str = client.get_current_time_iso()
            next_latest_notif_found = latest_notif_found

            some_params = atproto.models.AppBskyNotificationListNotifications.Params()
            some_params.limit = 10
            some_params.reasons = ["mention"]
            response = client.app.bsky.notification.list_notifications(some_params) # doesnt always get all recent notifications
            for notification in response.notifications:
                # skip old notifications
                notif_creation_time_str = notification.indexed_at.replace("T", " ").replace("Z", "+00:00")
                notif_creation_time = datetime.datetime.fromisoformat(notif_creation_time_str)
                too_old = notif_creation_time <= latest_notif_found
                if too_old and notification.is_read:
                    continue
                if notif_creation_time > latest_notif_found:
                    next_latest_notif_found = notif_creation_time
                
                # fetch post
                while True:
                    try:
                        post = client.get_post(atproto.AtUri.from_str(notification.uri).rkey, notification.author.did)
                        break
                    except:
                        pass
                
                # thank the mention
                print(f'Got new notification from: {notification.author.handle} at {notification.uri} saying \"{post.value.text}\"')
                client.like(notification.uri, notification.cid)

                # fact check post, or root of reply
                if (post.value.reply):
                    # if not post_fact_check(model, client, post.value.text, post.value.reply):
                    root_ref = post.value.reply.root
                    posts = client.get_posts([root_ref.uri]).posts
                    if len(posts) == 1:
                        root_post = posts[0]
                        post_fact_check(model, client, root_post.record.text, post.value.reply)
                    else:
                        print("failed to find root post")
                else:
                    root_ref = atproto.models.create_strong_ref(post)
                    reply_ref = atproto.models.AppBskyFeedPost.ReplyRef(parent=root_ref, root=root_ref)
                    post_fact_check(model, client, post.value.text, reply_ref)


            # mark notifications as processed (isRead=True)
            latest_notif_found = next_latest_notif_found
            client.app.bsky.notification.update_seen({'seen_at': last_seen_at_str})
            print('Successfully processed notifications. Last seen at:', last_seen_at_str)
            
            # chill a bit
            time.sleep(5)



if __name__ == "__main__":
    main()
