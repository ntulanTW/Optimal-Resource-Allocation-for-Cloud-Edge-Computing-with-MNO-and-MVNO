from poisson_arrival import beta
import os
import json
from parameters import *
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.size': 16
})

np.random.seed(rnd_seed)

# the traffic ratio over peek traffic of 24 hours in a day
# hour_traffic_ratio = [0.51, 0.42, 0.33, 0.31, 0.23, 0.23, 0.24, 0.22, 0.24, 0.33, 0.35, 0.52, 0.56, 0.56, 0.64, 0.8, 0.91, 0.97, 0.98, 0.95, 0.92, 0.965, 0.87, 0.8]
# hour 1~24
day_hour_traffic_ratio = [0.09, 0.09, 0.07, 0.07, 0.07, 0.13, 0.44, 0.73, 0.77, 0.78, 0.72, 0.48, 0.69, 0.69, 0.47, 0.26, 0.20, 0.19, 0.12, 0.10, 0.08, 0.07, 0.07, 0.07]

user_num = 300
machine_num = 300
out_files = ['./data/case4/', './baselines/VM Load Balance/data/case4/', './baselines/Random/data/case4/']
number_of_days = 7

def machine_generator(filename):
    id = 1
    _str = '{\n'
    for id in range(machine_num):
        _type = np.random.choice(['VoIP', 'IP_Video', 'FTP'])
        location = np.random.choice(['cloud', 'edge'])
        discount, max_cpu = 0.67, 1
        if location == 'edge':
            discount, max_cpu = 1, 0.6
        cpu = np.random.random() * max_cpu
        price = int(cpu * 250 * discount)
        _str += f'"{id}":{{"id":"{id}","task_type":"{_type}","location":"{location}","cpu_capacity":{cpu:.2f},"price":{price}}}'
        if id != machine_num - 1:
            _str += ',\n'
        else:
            _str += '\n'
    _str += '}'
    # save to each dir
    for dir in out_files:
        if not os.path.exists(dir):
            os.makedirs(dir)
        with open(dir + filename, 'w') as f:
            f.write(_str)

def task_events_generator(filename, days, hour_traffic_ratio):
    def event_gen(_type, cpu, bw_up_attr, bw_down_attr):
        return [event_id, 0, t, _type, str(np.random.randint(0, user_num)), cpu, beta(4, 4, 0.01, cpu - 0.005),
                beta(*bw_up_attr), beta(*bw_down_attr)]
    t = 0
    event_id = 0
    event_in = {}
    
    _str = '[\n'
    for i in range(days):
        if i % 7 < 5:
            r = 1
        else:
            r = 0.12
        for hour_ratio in hour_traffic_ratio:
            freqs = (voip_spe * hour_ratio * r, ipVideo_spe * hour_ratio * r, ftp_spe * hour_ratio * r)
            attrs = (("VoIP", voip_max_cpu, voip_bw_up_attr, voip_bw_down_attr), ("IP_Video", ipVideo_max_cpu, ipVideo_bw_up_attr, ipVideo_bw_down_attr),
                    ("FTP", ftp_max_cpu, ftp_bw_up_attr, ftp_bw_down_attr))
            while 1:
                # outcome events
                if t in event_in:
                    for event in event_in[t]:
                        event[1] = 1
                        event[2] = t
                        _str += json.dumps(event) + ',\n'
                        event_id += 1
                    del event_in[t]
                # income events
                for freq, attr in zip(freqs, attrs):
                    for _ in range(np.random.poisson(freq)):
                        event = event_gen(*attr)
                        interval = min(np.random.randint(1, 1000), 300) # maximum interval in google dataset is 5min
                        end_t = t + interval
                        if end_t not in event_in:
                            event_in[end_t] = []
                        event_in[end_t].append(event)
                        _str += json.dumps(event) + ',\n'
                        event_id += 1
                t += 1
                if t % 3600 == 0:
                    break
    for t, events in sorted(event_in.items(), key=lambda x: x[1]):
        for event in events:
            event[1] = 1
            event[2] = t
            _str += json.dumps(event) + ',\n'
            event_id += 1
    # delete the last ',' to make a valid list
    _str = _str[:-2] + '\n]'
    
    # save to each dir
    for dir in out_files:
        if not os.path.exists(dir):
            os.makedirs(dir)
        with open(dir + filename, 'w') as f:
            f.write(_str)

def plot():
    plt.figure()
    plt.title('traffic pattern in a day')
    plt.xlabel('hour')
    plt.ylabel('traffic ratio compare to peak value')
    plt.plot(np.arange(1, len(day_hour_traffic_ratio) + 1), day_hour_traffic_ratio)
    plt.savefig('data/daily_pattern')

if __name__ == '__main__':
    if not os.path.exists('./data'):
        os.makedirs('./data')
    plot()
    assert()
    machine_generator('machine_attributes.json')
    task_events_generator('task_events.json', number_of_days, day_hour_traffic_ratio)
    task_events_generator('history_data.json', number_of_days, day_hour_traffic_ratio)
    print(f'Finished generating, save result to {out_files}')