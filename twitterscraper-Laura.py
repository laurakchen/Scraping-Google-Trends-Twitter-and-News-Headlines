import codecs
import json
import pandas as pd
import numpy as np
import re as re
import time

from textblob import TextBlob
from twitterscraper import query_tweets

import datetime as dt

pd.options.mode.chained_assignment = None
# this enables us for rewriting dataframe to previous variable
from typing import List, Dict


#creates new dataframe to add data for each topic onto
tweet_df = pd.DataFrame()
tweet_df = tweet_df.assign(year_month=np.nan)


#specify the timeframe you want to scrape tweets from
begin_date = dt.date(2007, 1 , 1)
end_date = dt.date(2020,  7, 1)

#limit is the amount of tweets you want per each topic (set it to 100 so it doesn't run forever)
limit = 100
lang = 'english'

#function to scrape a single tweet and return the dataframe
def tweet(emp):
	tweets = query_tweets(emp , begindate = begin_date , enddate = end_date ,
						  limit = limit , lang = lang, poolsize=162)
	time.sleep(2)
	Df = pd.DataFrame(t.__dict__ for t in tweets)
	return Df

#regex to clean tweets
def clean_tweet(tweet):
	return ' '.join(re.sub('(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)', ' ', tweet).split())

#categorical sentiment analysis (I did not include this)
def analyze_sentiment(tweet):
	analysis = TextBlob(tweet)
	if analysis.sentiment.polarity > 0:
		return 'Positive'
	elif analysis.sentiment.polarity == 0:
		return 'Neutral'
	else:
		return 'Negative'

#sentiment annalysis using Textblob: subjectivity (number between 0 and 1)
def analyze_sentiment_subjectivity(tweet):
	return TextBlob(tweet).sentiment.subjectivity

#sentiment annalysis using Textblob: polarity (number between -1 and 1)
def analyze_sentiment_polarity(tweet):
	return TextBlob(tweet).sentiment.polarity


def twitterscraper(topics, tweet_df):
	counter = 0
	topic_tweets = pd.DataFrame()
	try:
		# loop through the array of topics, group by month and year, calculate # of words and sentiment score for each topic for each month
		for topic in topics:
			# for each topic, scrape the tweets
			topic_tweets = tweet(topic)
			# drop useless columns of data twitterscraper gives us
			topic_tweets.drop(
				columns=['tweet_id', 'has_media', 'hashtags', 'img_urls', 'is_replied',
						 'is_reply_to', 'likes', 'links', 'parent_tweet_id',
						 'reply_to_users', 'retweets', 'screen_name',
						 'timestamp_epochs', 'text_html', 'tweet_url', 'user_id',
						 'video_url', 'username', 'likes', 'replies'], inplace=True)
			# get the year and month and combine them (this sets all the days to 1, so we can keep it as a datetime variable and allows us to group by month and year together later)
			topic_tweets['year'] = pd.DatetimeIndex(topic_tweets['timestamp']).year
			topic_tweets['month'] = pd.DatetimeIndex(topic_tweets['timestamp']).month
			topic_tweets['year_month'] = pd.to_datetime(
				topic_tweets[['year', 'month']].assign(DAY=1))
			topic_tweets.drop(columns=['timestamp'], inplace=True)
			# cleans each tweet with the function in the codechunk above
			topic_tweets[topic + ' Clean Tweet'] = topic_tweets['text'].apply(
				lambda x: clean_tweet(x))
			# calculate polarity and subjectivity of each tweet
			topic_tweets[topic + " Sentiment Score-Polarity"] = topic_tweets[topic + ' Clean Tweet'].apply(lambda x: analyze_sentiment_polarity(x))
			topic_tweets[topic + " Sentiment Score-Subjectivity"] = topic_tweets[topic + ' Clean Tweet'].apply(lambda x: analyze_sentiment_subjectivity(x))

			# group by month-year pair, combines all tweets into a single string and averages the sentiment scores
			topic_tweets = topic_tweets.groupby(['year_month'], as_index=False).agg(
				{topic + " Clean Tweet": ' '.join, topic + " Sentiment Score-Polarity": 'mean',
				 topic + " Sentiment Score-Subjectivity": 'mean'})

			# counts the words in each tweet string combo (# of words tweeted every month for the topic)
			topic_tweets[topic] = topic_tweets[topic + " Clean Tweet"].str.split().str.len()

			# export each word's sentiment and cleaned tweet to a separate csv
			topic_tweets.to_csv(topic+'.csv')
			print("topic_tweets to csv worked!")

			print(topic_tweets.head(5))
			counter += 1
			print(counter, topic)

			# append the numbers calculated for each topic to the combined dataframe as new columns
			tweet_df = pd.merge(tweet_df, topic_tweets, on='year_month', how='outer')
			tweet_df.drop(topic + ' Clean Tweet', axis=1, inplace=True)
	except:
		print(counter)
		print(tweet_df)
		tweet_df = pd.merge(tweet_df, topic_tweets, on='year_month', how='outer')
	return tweet_df


top1000words = pd.read_csv('top1000words.csv', header=None, names=["word"])

# specify what word index to start scraping from
begin_ind = 90
end_ind = 100
topics = top1000words["word"].iloc[begin_ind:end_ind].to_list()
tweet_df = twitterscraper(topics, tweet_df)

# clean up final dataset by sorting dates and dropping unwanted cols
tweet_df.sort_values(by='year_month', inplace=True)

# name your final dataset's csv filename based on the words you started scraping
tweet_df.to_csv('twitterFinal(' + str(begin_ind) + '-' + str(end_ind) + ').csv')
print("SUCCESS!!")

