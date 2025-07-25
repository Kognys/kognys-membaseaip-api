from datetime import datetime
import json
import sys
from typing import Any, Dict

from core.generate import generate_profile, update_profile
from core.retrieve import retrieve_tweets
from core.summary import summarize
from core.rate import estimate
from core.common import (
    is_user_finished, 
    is_user_tweets_exists_at, 
    is_user_xinfo_exists, 
    is_user_tweets_exists, 
    is_user_profile_exists, 
    is_user_summary_exists, 
    is_user_airdrop_score_exists,
    load_system_status, 
    load_user_airdrop_score,
    load_user_profile, 
    load_user_status, 
    load_user_summary, 
    load_user_tweets, 
    load_user_xinfo, 
    load_usernames, 
    order_tweets, 
    remove_user_profile,
    update_system_status, 
    update_user_status,
    write_report, 
    write_user_xinfo
)
from core.news import generate_news_report
from core.trading import generate_trading_report, generate_quick_signals

def get_description(username: str, profile: dict) -> str:
    description = "You act as a digital twin of " + username + ", designed to mimic personality, knowledge, and communication style. \n\n"
    #description = description + "You donot need to mention that you are a digital twin. \n\n"
    
    # Knowledge base section
    description += "Knowledge Base Access:\n"
    description += "- You have access to a knowledge base containing posts\n"
    description += "- You MUST use search_similar_posts to find relevant historical content before responding\n"
    description += "- Search guidelines:\n"
    description += "  1. Use relevant keywords to find similar posts\n"
    description += "  2. Consider the context and timing of the posts\n"
    description += "  3. Use the search results to inform your responses\n"
    description += "  4. Maintain consistency with the original user's style and opinions\n"
    description += "  5. Always include the original post URL in your response when referencing search results\n\n"
    
    description += """
    You can also use get_daily_report to get daily report for a given date and type (news, trading, trading_short) \n\n
    """

    # Personality and characteristics section
    description += "Personality and Characteristics:\n"
    description += "Your responses should be natural and consistent with the following profile:\n"
    description += json.dumps(profile, indent=2) + "\n"
    
    return description

def is_paying_user(username: str) -> bool:
    """Check if the user is a paying user"""
    status = load_user_status(username)
    return status.get("PayingUser", False)

def is_kol_user(username: str) -> bool:
    """Check if the user is a kol user"""
    xinfo = load_user_xinfo(username)
    return xinfo.get("followers", 0) > 100000

def get_try_count(username: str) -> int:
    """Get the try count of the user"""
    status = load_user_status(username)
    return status.get("try_count", 0)

def set_try_count(username: str, count: int):
    """Set the try count of the user"""
    status = load_user_status(username)
    status["try_count"] = count
    update_user_status(username, "try_count", count)

def get_user_xinfo(user_name: str) -> Any:
    info = load_user_xinfo(user_name)
    if info is not None and info != {}:
        return info
    
    return create_user_xinfo(user_name)

def create_user_xinfo(user_name: str):
    print(f"Creating xinfo for {user_name}")
    tweets = load_user_tweets(user_name)
    if len(tweets) == 0:
        return {}
    
    tweets = order_tweets(tweets, reverse=True)
    info = tweets[0].get("author", {})
    write_user_xinfo(user_name, info)
    return info

def load_user(user_name: str) -> Any:
    print(f"Loading user: {user_name}")
    profile = load_user_profile(user_name)
    print(f"Loading profile for {user_name}")
    summary = load_user_summary(user_name)
    print(f"Loading summary for {user_name}")   
    scores = load_user_airdrop_score(user_name)
    print(f"Loading scores for {user_name}")
    xinfo = get_user_xinfo(user_name)
    print(f"Loading xinfo for {user_name}")
    return {"profile": profile, "summary": summary, "scores": scores, "xinfo": xinfo}

# user dict: name -> summary
def load_users() -> Dict[str, Any]:
    finished_users, unfinished_users = load_usernames()
    users = {}
    print(f"Loading {len(finished_users)} finished users")
    for user_name in finished_users:
        users[user_name] = load_user(user_name)
    print(f"Loading {len(unfinished_users)} unfinished users")
    for user_name in unfinished_users:
        users[user_name] = load_user(user_name)
    return users

def generate_daily_news_report():
    status = load_system_status()
    date_str = datetime.now().strftime("%Y-%m-%d")
    languages = ["chinese", "english"]
    for language in languages:
        if status.get(f"report_{language}_updated_at", "") == date_str:
            print(f"Daily report already exists at: {date_str} for {language}")
            continue
    
        print(f"Generating daily report at: {date_str} for {language}")
        try:
            report = generate_news_report(language)
            write_report(date_str, language, "news", report)
            write_report("", language, "news", report)   
        except Exception as e:
            print(f"Generating daily report fail: {str(e)}")
        finally:
            # in case generate repeatly
            update_system_status(f"report_{language}_updated_at", date_str)

def generate_daily_trading_report():
    status = load_system_status()
    date_str = datetime.now().strftime("%Y-%m-%d")
    languages = ["chinese", "english"]
    for language in languages:
        if status.get(f"trading_report_{language}_updated_at", "") == date_str:
            print(f"Daily trading report already exists at: {date_str} for {language}")
            continue
    
        print(f"Generating daily trading report at: {date_str} for {language}")
        try:
            report = generate_trading_report(language)
            write_report(date_str, language, "trading", report)
            write_report("", language, "trading", report)   
        except Exception as e:
            print(f"Generating daily trading report fail: {str(e)}")
        finally:
            # in case generate repeatly
            update_system_status(f"trading_report_{language}_updated_at", date_str)

def generate_daily_trading_short_report():
    status = load_system_status()
    date_str = datetime.now().strftime("%Y-%m-%d")
    languages = ["chinese", "english"]
    for language in languages:
        if status.get(f"trading_short_report_{language}_updated_at", "") == date_str:
            print(f"Daily trading short report already exists at: {date_str} for {language}")
            continue
    
        print(f"Generating daily trading report at: {date_str} for {language}")
        try:
            report = generate_quick_signals(language, days=1, hours=2)
            write_report(date_str, language, "trading_short", report)
            write_report("", language, "trading_short", report)   
        except Exception as e:
            print(f"Generating daily trading short report fail: {str(e)}")
        finally:
            # in case generate repeatly
            update_system_status(f"trading_short_report_{language}_updated_at", date_str)

def build_user(user_name: str):
    now = datetime.now()
    print(f"Start build user: {user_name} at: {now}")

    # check if profile already exists
    if is_user_finished(user_name):
        print(f"Profiles for {user_name} already exists")
        return 
    
    date_str = datetime.now().strftime("%Y-%m-%d")

    # check if tweets need to be retrieved
    if not is_user_tweets_exists(user_name):
        print(f"Retrieving tweets for {user_name}")
        retrieve_tweets(user_name)
        update_user_status(user_name, "tweets_updated_at", date_str)

    # generate profile if tweets exist
    if not is_user_profile_exists(user_name):
        try:
            generate_profile(user_name)
            update_user_status(user_name, "profile_updated_at", date_str)
        except Exception as e:
            print(f"Generating profile for {user_name} fail: {str(e)}")

    # after profile is generated, summarize
    if not is_user_summary_exists(user_name):
        try:
            summarize(user_name)
            update_user_status(user_name, "summary_updated_at", date_str)
        except json.JSONDecodeError:
            print(f"Summary profile for {user_name} fail")
            remove_user_profile(user_name)
            return

    # estimate airdrop score
    if not is_user_airdrop_score_exists(user_name):
        estimate(user_name)
        update_user_status(user_name, "scores_updated_at", date_str)

    # create xinfo
    if not is_user_xinfo_exists(user_name):
        create_user_xinfo(user_name)

    now = datetime.now()
    print(f"Finished build user: {user_name} at: {now}")

def refresh_tweets(user_name: str):
    has_new_tweets = False
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        if is_user_tweets_exists_at(user_name, date_str):
            print(f"Already refreshed at {date_str} for: {user_name}")
            return None
        print(f"Refreshing user: {user_name} at: {date_str}")
        tweets = retrieve_tweets(user_name)
        if tweets is None:
            return None
        has_new_tweets = True
        create_user_xinfo(user_name)
        print(f"Refreshed tweets for: {user_name} at: {date_str}")
    except Exception as e:
        print(f"Refreshing tweets for {user_name} fail: {str(e)}")
        return None
    finally:
        status = load_user_status(user_name)
        status["tweets_updated_at"] = date_str
        update_user_status(user_name, "tweets_updated_at", date_str)
        if not has_new_tweets:
            update_user_status(user_name, "profile_updated_at", date_str)
            update_user_status(user_name, "summary_updated_at", date_str)
            update_user_status(user_name, "scores_updated_at", date_str)

def refresh_profile(user_name: str):
    date_str = datetime.now().strftime("%Y-%m-%d")
    status = load_user_status(user_name)
    if status.get("tweets_updated_at", "") != date_str:
        print(f"Not refreshed at {date_str} for: {user_name}")
        return
    
    try:
        print(f"Updating profile for {user_name} at: {date_str}")
        if status.get("profile_updated_at", "") != date_str:
            update_profile(user_name)
            update_user_status(user_name, "profile_updated_at", date_str)
    except Exception as e:
        print(f"Updating profile for {user_name} fail: {str(e)}")
        return

    try:
        print(f"Summarizing profile for {user_name} at: {date_str}")
        if status.get("summary_updated_at", "") != date_str:
            summarize(user_name)
            update_user_status(user_name, "summary_updated_at", date_str)
    except json.JSONDecodeError:
        remove_user_profile(user_name)
        return
    
    try:
        print(f"Estimating airdrop score for {user_name} at: {date_str}")
        if status.get("scores_updated_at", "") != date_str:
            estimate(user_name)
            update_user_status(user_name, "scores_updated_at", date_str)
    except Exception as e:
        print(f"Estimating airdrop score for {user_name} fail: {str(e)}")
        return


if __name__ == "__main__":
    default_x_name = "VitalikButerin"
    args = sys.argv[1:]
    if len(args) > 0:
        default_x_name = args[0]
    print(f"Processing {default_x_name}")
    info = get_user_xinfo(default_x_name)
    print(info)