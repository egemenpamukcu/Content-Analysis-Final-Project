import csv
import multiprocessing

import utils #twitter.utils as utils
import auth #twitter.auth as auth
import parameters as p
from datetime import datetime
from tqdm import tqdm

class user_likes:
    def __init__(self, key_number, multiprocess=None):
        self.twitter_keys, self.api = auth.auth(index=key_number)
        self.filename = "generic.json"
        self.filename2 = "users_likes.json"
        if multiprocess is not None:
            self.filename2 = "users_likes"+str(multiprocess)+".json"

    def all_likes(self, user_id):
        file = utils.update_json("users.json")
        if user_id in file.data:
            user = file.data[user_id]
            fav_count = user["favorites_count:"]
            self.filename = user["query"]+".json"
        else:
            user = self.api.get_user(id=user_id)
            fav_count = user.favourites_count

        pages = min(int(fav_count/20), p.MAX_PAGES_PER_USER)    
        for page in (range(1, pages)):
            self.likes(user_id, page=page)

    def likes(self, user_id, page=1):
        try:
            if self.check(user_id, page):
                results = self.api.favorites(id=user_id, page=page, tweet_mode="extended", trim_user=True)
                self.save_posts(user_id, results)
                self.save_queries(user_id, page)
        except Exception as ex:
            print(ex)

    def save_queries(self, user_id, page):
        file_handle = open("user_favs.csv", "a")
        with file_handle as csv_file:
            row = [user_id, page,] #datetime.today()]
            writer = csv.writer(csv_file)
            writer.writerow(row)

    def check(self, user_id, page):
        with open("user_favs.csv", "r") as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                if row[0:2] == [str(user_id), str(page)]:
                    print("already queried")
                    return False
        return True

    def save_posts(self, user_id, results):

        updater_posts = utils.update_json(self.filename)
        updater_user  = utils.update_json(self.filename2)
        for result in results:
            if result.id_str in updater_posts.data:
                updater_posts.data[result.id_str]["liked_by"] += [user_id]
                updater_posts.data[result.id_str]["liked_by"] = list(set(updater_posts.data[result.id_str]["liked_by"]))
                continue
            
            hashtags = [hashtag["text"] for hashtag in result.entities["hashtags"]] if "hashtags" in result.entities else []
            media = [media["media_url_https"] for media in result.entities["media"]] if "media" in result.entities else []
            
            dic = {
                result.id_str:{
                    "creator_id": result.user.id,
                    "created_at":result.created_at,
                    "liked_by": [user_id],
                    "text": result.full_text,
                    "hashtags": hashtags,
                    "media": media}
                    }
                    
            updater_posts.data.update(dic)

            if user_id in updater_user.data:
                updater_user.data[user_id]["posts_liked"]+=[result.id_str]
                updater_user.data[user_id]["posts_liked"] = list(set(updater_user.data[user_id]["posts_liked"]))
        updater_posts.write()
        updater_user.write()

def main():
    file = utils.update_json("users.json")
    for i,id in enumerate(tqdm(file.data.keys())):
        s = user_likes(key_number=i%4)
        s.all_likes(id)

if __name__ == "__main__":
    main()