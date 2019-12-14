from flask import Flask, request
import slack
import sched, time, json, _thread, os, datetime

app = Flask(__name__)

SLACK_API_TOKEN = os.environ['SLACK_API_TOKEN']
client = slack.WebClient(token=SLACK_API_TOKEN)

ONE_DAY = 86400


@app.route('/', methods=['POST'])
def schedule_event():
    """
    Receives an event - Time & Message - schedules the event in a new thread.
    """
    data = request.get_json(force=True)
    schedule_time, msg = data['time'], data['message']
    epoch_time = convert_to_epoch(schedule_time)
    _thread.start_new_thread(schedule_msg, args=(epoch_time, msg,))
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


def schedule_msg(schedule_time, msg):
    """
    :param schedule_time: Epoch format for a given time to execute the message
    :param msg: text
    """
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enterabs(schedule_time, 1, broadcast_message, (msg, scheduler))
    scheduler.run()


def get_users():
    """
    Return the users id list of the current workspace
    """
    users_call = client.api_call('users.list')
    if users_call.get('ok'):
        return [user['id'] for user in users_call['members'] if user['deleted'] is False]
    return []


def broadcast_message(msg, scheduler):
    """
    :param msg: Message to be sent to all users.
    :param scheduler: Scheduler object that will schedule the next message

    Re-enables the scheduler to enter in 24 hours and posts the message directly
    to all users.
    """
    scheduler.enter(ONE_DAY, 1, broadcast_message, (msg, scheduler))
    users = get_users()
    for user in users:
        client.chat_postMessage(channel=user, text=msg)


def convert_to_epoch(scheduled_time):
    """
    :param scheduled_time: Text format "13:30" for a given time
    :return: Returns the given scheduled_time in Epoch format
    """
    hour, min = list(map(lambda x: int(x), scheduled_time.split(':')))
    dt = datetime.datetime.now().replace(hour=hour, minute=min, second=0, microsecond=0)
    epoch_time = dt.strftime('%s')
    return float(epoch_time)


if __name__ == '__main__':
    app.run()
