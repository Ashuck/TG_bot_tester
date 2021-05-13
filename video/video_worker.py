import requests
import datetime
import os
import shutil
import sqlite3


def get_files(p):
    for f in os.listdir(p):
        full_path = os.path.join(p, f)
        if os.path.isfile(full_path):
            yield full_path
        else:
            for f2 in get_files(full_path):
                yield f2



def move_to_docker(path):
    # Перемещение в папку докера
    base_name = os.path.basename(path)
    new_loc = f'{mount_docker}/{base_name}'
    # os.system(f'ln -s "{path}" "{new_loc}"')
    shutil.copy(path, new_loc)
    data_folder = new_loc.replace(".mp4", "")

    return base_name, data_folder



def move_to_ftp(data_folder, u_p):
    # Перемещение в папку для ftp
    user_path_folders = u_p.split('/')[1:-1]
    tmp = mount_data
    for i in user_path_folders: # надо создать папки пользователя в папке ftp
        tmp += '/' + i
        os.system(f'mkdir "{tmp}"')
    # print(f'mv "{data_folder}" "{tmp}"')
    os.system(f'mv "{data_folder}" "{tmp}"')
    


mount_next = "/mnt/nextcloudrawdata/data"
mount_docker = "/home/container_folder/tmp_video"
mount_data = "/mnt/ftp_output"
url = "http://127.0.0.1:5000/SERVICEF"
data = {"type": "video"}

os.system('mkdir ' + mount_docker)
path_to_db = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(f"{path_to_db}/paths.db") 
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS paths (path text, user text, result text)""")
conn.commit()

os.system(f'rm -r {mount_docker}/*')

while True:
    for item in get_files(mount_next):
        user_path = item.replace(mount_next, "")
        cursor.execute(f"SELECT * FROM paths WHERE path = '{user_path}' AND result = ''")

        if cursor.fetchall():
            continue

        user = user_path.split('/')[1]
        item_type = item.split('.')[-1]
        # print(user_path, user)
        if item_type.lower() == 'mp4':

            base_name, data_folder = move_to_docker(item)
            
            # Отправка на обработку в докер
            data['path'] = "./tmp_video/" + base_name
            print(data)
            req = requests.post(url, json=data).json()
            if req["errorCode"] == "":
                move_to_ftp(data_folder, user_path)
                cursor.execute(f"INSERT INTO paths VALUES ('{user_path}','{user}', '')")
            else:
                cursor.execute(f"INSERT INTO paths VALUES ('{user_path}','{user}', '{req['errorCode']}')")
            conn.commit()
            os.system(f'rm -r {mount_docker}/*')

        elif item_type.lower() == 'mov':
            base_name = os.path.basename(item)
            base_name_mp4 = base_name.replace('.' + item_type, ".mp4")

            os.system(f'ffmpeg -i {item} -q:v 0 {mount_docker}/{base_name_mp4}')
            print(data)
            data['path'] = "./" + base_name_mp4
            req = requests.post(url, json=data).json()
            if req["errorCode"] == "":
                data_folder = f'{mount_docker}/{base_name_mp4[:-4]}'
                move_to_ftp(data_folder, user_path)
                cursor.execute(f"INSERT INTO paths VALUES ('{user_path}','{user}', '')")
            else:
                cursor.execute(f"INSERT INTO paths VALUES ('{user_path}','{user}', '{req['errorCode']}')")
            conn.commit()
            os.system(f'rm -r {mount_docker}/*')