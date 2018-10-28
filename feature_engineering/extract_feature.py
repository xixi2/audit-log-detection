import json
import os
import operator
import time
import subprocess

ROOT_DIR = os.path.dirname(os.getcwd())
TOP_DIR = 'learn_final_r1'
SUB_DIR = 'inter'
FEATURE_FILE = 'event_list.txt'
FEATURE_FILE_PREFIX = 'event_list'
FEATURE_UNIQUE_FILE = 'event_unique_list.txt'


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
    :param event_list: 同一个进程号对应的多个事件,这里要求event_list不为空
    :return:
        continuous_event_list：一个列表，其中每个元素也是一个列表，列表中的所有事件连续
    """
    # print('----------split_event_list_into_continuous_list--------------')
    # print('event_list: {0}'.format(event_list))
    # print('len of event_list: {0}'.format(len(event_list)))

    continuous_event_list = []
    n = len(event_list)
    continuous_event_list.append([])
    continuous_event_list[0].append(event_list[0][1])
    k = 0

    for i in range(1, n):
        time_first = event_list[i - 1][0]
        time_last = event_list[i][0]
        flag = is_continuous_event(time_first, time_last) == 1
        if flag:
            # continuous_event_list[k].append(event_list[i])        # 将每个event中的时间和string_id都保存下来
            continuous_event_list[k].append(event_list[i][1])  # 仅保存每个event中的string_id
        else:
            continuous_event_list.append([])
            k += 1
            # continuous_event_list[k].append(event_list[i])        # 同上
            continuous_event_list[k].append(event_list[i][1])  # 同上
    return continuous_event_list


def generate_q_gram_event(continuous_list, q):
    """
    :param continuous_list:连续事件的列表，用于产生q-gram-event
    :param q:
    :return:
    """
    n = len(continuous_list)
    q_gram_event = []
    for i in range(n - q + 1):
        seg = tuple(continuous_list[i:i + q])
        q_gram_event.append(seg)
    return q_gram_event


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
        # print('q*************************:{0}'.format(q))
        for item in continuous_event_list:
            q_gram_event = generate_q_gram_event(item, q)
            if q_gram_event:
                # print('continuous_event_list q_ngram_event: {0}'.format(q_gram_event))
                events_of_one_pid.extend(q_gram_event)
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
    total_events_num = 0
    ignored_events_num = 0
    events_of_one_json_file = []
    for i in range(len(processes)):
        single_process_events = processes[i]['events']  # single_process_events是一个dict列表，每个dict是单个事件描述信息
        origin_events_list = []  # 属于同一进程号的多个事件

        for j in range(len(single_process_events)):
            if single_process_events[j]['ignored'] is True:  # ignore is True代表该事件被忽略
                ignored_events_num += 1
                continue
            else:
                timestamp = single_process_events[j]['time']
                string_id = single_process_events[j]['string_id']
                origin_events_list.append((timestamp, string_id))

        if origin_events_list:
            events_of_one_pid = generate_events_of_one_pid(origin_events_list)
            events_of_one_json_file.extend(events_of_one_pid)
            total_events_num += len(events_of_one_pid)

    f.close()
    return events_of_one_json_file, total_events_num, ignored_events_num


def extract_events_from_all_json_file():
    file_path = os.path.join(ROOT_DIR, TOP_DIR, SUB_DIR)
    file_list = os.listdir(file_path)
    events_total = 0
    ignored_total = 0
    for file in file_list:
        file_name = os.path.join(file_path, file)
        print('file_name:{0}'.format(file_name))
        events_of_one_json_file, events_num, ignored_events_num = extract_event_from_one_json_file(file_name)
        events_total += events_num
        ignored_total += ignored_events_num
        write_events_to_file(events_of_one_json_file)

    print('------------------------events_total--------------------------')
    print('events_total: {0}'.format(events_total))
    print('ignored_total: {0}'.format(ignored_total))
    print('file_list: {0}'.format(len(file_list)))
    print('************************events_total**************************')


def execute_system_command(command):
    print('command: {0}'.format(command))
    out_put = subprocess.check_output(command, shell=True)
    return out_put


def remove_duplicate_lines(source_file=FEATURE_FILE, dst_file=FEATURE_UNIQUE_FILE):
    command = 'sort -u ' + source_file + '-->' + dst_file
    execute_system_command(command)
    print('successfully remove all duplicate lines!')


def count_lines(file_name):
    command = 'wc -l ' + file_name
    output = execute_system_command(command)
    print('{0}:{1}'.format(file_name, output))


def single_testing():
    """
    这个仅仅为了方便测试
    :return:
    """
    file_name = 'cuckoo_00a0dad1676bb65fd3c50e83c481219b25119f2d_anon.json'
    file_path = os.path.join(ROOT_DIR, TOP_DIR, SUB_DIR, file_name)
    print('ROOT_DIR:{0}'.format(ROOT_DIR))
    print('file_path:{0}'.format(file_path))
    events_of_one_json_file, total_events_num, ignored_events_num = extract_event_from_one_json_file(file_path)
    print('len of events_of_one_json_file:{0}'.format(len(events_of_one_json_file)))
    print('***********************************************************')
    print(events_of_one_json_file[:2])
    print('***********************************************************')
    for i in range(4):
        print(events_of_one_json_file[i])


def multi_testing():
    # 去重
    file_name_list = [
        # 'cuckoo_00a0dad1676bb65fd3c50e83c481219b25119f2d_anon.json',
        # 'cuckoo_00a0dad1676bb65fd3c50e83c481219b25119f2d_anon.json',
        'cuckoo_00a4a2b83076c54e9c3bfbd912d7ea87cf9bd914_anon.json',
        'cuckoo_00a4a2b83076c54e9c3bfbd912d7ea87cf9bd914_anon.json',
        'cuckoo_00c6f548369e8640221af3aedec3a8bbefd24ba3_anon.json',
        'cuckoo_00c6f548369e8640221af3aedec3a8bbefd24ba3_anon.json',
    ]
    sum = 0
    events_set = set([])
    for file_name in file_name_list:
        file_path = os.path.join(ROOT_DIR, TOP_DIR, SUB_DIR, file_name)
        events_of_one_json_file, total_events_num, ignored_events_num = extract_event_from_one_json_file(file_path)
        events_set = events_set | set(events_of_one_json_file)
        sum += total_events_num
        print('------------------------------------------------------------------------')
        print('file_path:{0}, total_events_num: {1}'.format(file_path, total_events_num))
        print('len of events_of_one_json_file:{0}'.format(len(events_of_one_json_file)))
        print('**************************************************************************')
    print('len of events_set: {0}'.format(len(events_set)))
    print('sum: {0}'.format(sum))
    print('sum - len(events_set): {0}'.format(sum - len(events_set)))


if __name__ == '__main__':
    start = time.time()
    # single_testing()
    # multi_testing()
    extract_events_from_all_json_file()
    # remove_duplicate_lines()
    end = time.time()
    secs = (end - start) / 60
    # count_lines(FEATURE_FILE)
    # count_lines(FEATURE_UNIQUE_FILE)
    print('start:{0}, end:{1}'.format(start, end))
    print('secs:{0}'.format(secs))
