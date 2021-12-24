# coding=utf-8
import json
# save data to json file
def store(data,filename = 'data.json'):
    with open(filename, 'w') as fw:
        # json_str = json.dumps(data)
        # fw.write(json_str)
        # 
        json.dump(data,fw)
# load json data from file
def load(filename = 'data.json'):
    with open(filename,'r') as f:
        data = json.load(f)
        return data
def test():
    args = sys.argv
    if len(args)==1:
        print('Hello, world!')
    elif len(args)==2:
        print('Hello, %s!' % args[1])
    else:
        print('Too many arguments!')

if __name__ == '__main__':
    a = {"a":1}
    store(a)