from locust import HttpLocust, TaskSet, task
import locust.events
import time
import random
import socket
import atexit
import os

CLIENT_ID = [4948, 6462, 4777, 7645, 6931, 7562, 7052, 4777, 4950, 6744, 450, 6399, 2467, 6809, 4637, 4589, 6199, 4720, 7348, 7434, 7118, 4589, 3251];
URL_FORMAT = "/tsdb/%s/%d/?start_time=%s&end_time=%s&windows_days=%d&timezone=%s"
URL_NAME_FORMAT = "%s_%d_%s"
DATE_RANGES = {
    "recent_12month": {
        "start_date": "2018-01-23T00:00:00",
        "end_date": "2019-01-26T00:00:00"

    },
    "recent_6month":{
        "start_date": "2018-06-23T00:00:00",
        "end_date": "2019-01-26T00:00:00"
    },
    "recent_3month":{
        "start_date": "2018-10-23T00:00:00",
        "end_date": "2019-01-26T00:00:00"
    },
    "recent_1month":{
        "start_date": "2018-12-23T00:00:00",
        "end_date": "2019-01-26T00:00:00"
    },
    "recent_2week":{
        "start_date": "2019-01-13T00:00:00",
        "end_date": "2019-01-26T00:00:00"
    },
    "recent_week":{
        "start_date": "2019-01-20T00:00:00",
        "end_date": "2019-01-26T00:00:00"
    }

}

INPUT_DATE_RANGES = os.environ['INPUT_DATE_RANGES'].split(",")
INPUT_QUERIES = os.environ['INPUT_QUERIES'].split(",")
INPUT_WINDOW = int(os.environ['INPUT_WINDOW'])
INPUT_TIMEZONE = os.environ['INPUT_TIMEZONE']
GRAPHITE_HOST = os.environ['GRAPHITE_HOST']


def generate_urls(client_ids, date_ranges, queries, window_days, timezone):
    urls = {}
    for client_id in client_ids:
        for date_range in date_ranges:
            for query in queries:
                url = URL_FORMAT % (
                    query, client_id, DATE_RANGES[date_range]["start_date"], DATE_RANGES[date_range]["end_date"], window_days, timezone)
                urls[URL_NAME_FORMAT % (query, client_id, date_range)] = url
    return urls





class UserTasks(TaskSet):
    # one can specify tasks like this
    #tasks = [index(self, )]


    @task
    def index(self):
        urls = generate_urls(CLIENT_ID, INPUT_DATE_RANGES, INPUT_QUERIES, INPUT_WINDOW, INPUT_TIMEZONE)
        random_keys = list(urls.keys())
        random.shuffle(random_keys)
        for key in random_keys:
            self.client.get(urls[key], name=key)


class WebsiteUser(HttpLocust):

    sock = None

    def __init__(self):
        super(WebsiteUser, self).__init__()
        self.sock = socket.socket()
        self.sock.connect( (GRAPHITE_HOST, 2003) )
        locust.events.request_success += self.hook_request_success
        locust.events.request_failure += self.hook_request_fail
        atexit.register(self.exit_handler)

    def exit_handler(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def hook_request_success(self, request_type, name, response_time, response_length):
        payload = "%s %d %d\n" % ("analytics.performance." + name.replace('_', '.'), response_time,  time.time())
        self.sock.send(payload.encode())

    def hook_request_fail(self, request_type, name, response_time, exception):
        self.request_fail_stats.append([name, request_type, response_time, exception])

    min_wait = 2000
    max_wait = 5000
    task_set = UserTasks
