import json
import os
import operator
import time

ROOT_DIR = os.path.dirname(os.getcwd())
TOP_DIR = 'learn_final_r1'
SUB_DIR = 'inter'
FEATURE_FILE = 'event_list.txt'


def generate_q_gram_event(continuous_list, q):
    """
    :param continuous_list:连续事件的列表，用于产生q-gram-event
    :param q:
    :return:
    """
    n = len(continuous_list)
    q_gram_event = []
    for i in range(n - q + 1):
        seg = continuous_list[i:i + q]
        q_gram_event.append(seg)
    return q_gram_event


def grab_last_num(str):
    pos = str.rfind('.')
    if pos == -1:
        num = 0
    else:
        num = int(str[pos + 1:])
    return num


def is_continuous_event(time_first, time_last):
    """
    判断两个事件是否连续
    :param time_first: 第一个事件的时间
    :param time_last: 第二个事件的时间
    :return:
    """
    try:
        num_first = grab_last_num(time_first)
        num_last = grab_last_num(time_last)
        if num_first + 1 == num_last:
            return 1
        return 0
    except Exception as e:
        print('-------------error:{0}------------------'.format(e))


def split_event_list_into_continuous_list(event_list):
    """
    :param event_list: 同一个进程号对应的多个事件
    :return:
        continuous_event_list：一个列表，其中每个元素也是一个列表，列表中的所有事件连续
    """
    continuous_event_list = []
    n = len(event_list)
    continuous_event_list.append([])
    continuous_event_list[0].append(event_list[0])
    k = 0

    for i in range(1, n):
        time_first = event_list[i - 1][0]
        time_last = event_list[i][0]
        flag = is_continuous_event(time_first, time_last) == 1
        if flag:
            continuous_event_list[k].append(event_list[i])
        else:
            continuous_event_list.append([])
            k += 1
            continuous_event_list[k].append(event_list[i])
    return continuous_event_list


def generate_events_of_one_pid(event_list):
    """
    :param event_list:输入的同一进程号对应的事件
    :return:
    """
    event_list = sorted(event_list, key=operator.itemgetter(0))
    continuous_event_list = split_event_list_into_continuous_list(event_list)
    events_of_one_pid = []
    q_gram_set = (1, 2, 3)
    for q in q_gram_set:
        for item in continuous_event_list:
            q_ngram_event = generate_q_gram_event(item, q)
            events_of_one_pid.extend(q_ngram_event)
    return events_of_one_pid


def write_events_to_file(event_list):
    f = open(FEATURE_FILE, 'a+')
    for item in event_list:
        for event in item:
            if event != item[0]:
                f.write(',')
            f.write(event[1])
        f.write('\n')
    f.close()


def extract_event_from_one_json_file(file_name):
    """
    :param file_name:
    :return:
    """
    f = open(file_name, 'r')
    data = json.load(f)
    processes = data['Processes']  # processes是一个dict的列表，每个dict是一个进程的所有events
    process_num = len(processes)
    for i in range(process_num):
        single_process_events = processes[i]['events']  # single_process_events是一个dict列表，每个dict是单个事件描述信息
        event_num = len(single_process_events)
        origin_events_list = []  # 属于同一进程号的多个事件
        for j in range(event_num):
            temp = []
            temp.append(single_process_events[j]['time'])
            temp.append(single_process_events[j]['string_id'])
            origin_events_list.append(tuple(temp))
        events_of_one_pid = generate_events_of_one_pid(origin_events_list)
        write_events_to_file(events_of_one_pid)
    f.close()


def extract_events_from_all_json_file():
    file_path = os.path.join(ROOT_DIR, TOP_DIR, SUB_DIR)
    file_list = os.listdir(file_path)
    for file in file_list:
        file_name = os.path.join(file_path, file)
        print('file_name:{0}'.format(file_name))
        extract_event_from_one_json_file(file_name)


def testing():
    """
    这个仅仅为了方便测试
    :return:
    """
    file_name = 'cuckoo_00a0dad1676bb65fd3c50e83c481219b25119f2d_anon.json'
    file_path = os.path.join(ROOT_DIR, TOP_DIR, SUB_DIR, file_name)
    print('ROOT_DIR:{0}'.format(ROOT_DIR))
    print('file_path:{0}'.format(file_path))
    extract_event_from_one_json_file(file_path)


if __name__ == '__main__':
    start = time.time()
    extract_events_from_all_json_file()
    end = time.time()
    secs = (end - start) / 60
    print('start:{0}, end:{1}'.format(start, end))
    print('secs:{0}'.format(secs))
