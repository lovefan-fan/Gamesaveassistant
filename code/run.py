import json
import shutil
import os
import subprocess
import sys
import threading
import time
from tkinter import ttk, filedialog, messagebox,Listbox, Button

import psutil
import tkinter as tk

# 初始化环境变量
# 游戏存档位置
cache_dir = os.path.join(os.environ['USERPROFILE'], "AppData", "Local", "Gamesavebackup", "Cache")
unzip_dir = os.path.join(os.environ['USERPROFILE'], "AppData", "Local", "Gamesavebackup")

#---方法库---
# 压缩文件夹
def compress_folder(source_folder, output_zip):
    """
    压缩指定的文件夹为ZIP格式

    :param source_folder: 要压缩的文件夹路径
    :param output_zip: 压缩文件保存的完整路径（不包括扩展名）
    """
    if not os.path.isdir(source_folder):
        raise ValueError("指定的路径不是一个有效的文件夹")

    # 获取文件夹名称作为压缩包名称
    folder_name = os.path.basename(source_folder)
    output_zip = os.path.join(os.path.dirname(output_zip), folder_name)

    # 创建zip压缩包，使用shutil的make_archive方法
    shutil.make_archive(output_zip, 'zip', source_folder)
    print(f"文件夹已成功压缩至 {output_zip}.zip")
    return folder_name+'.zip'
    # compress_folder("./测试压缩/TSMpackagemanager", "./测试压缩/解压目录")
# 解压
def extract_zip(zip_path, extract_to=None):
    """
    解压 ZIP 文件到指定目录

    :param zip_path: ZIP 文件的路径
    :param extract_to: 解压后的文件保存路径。默认为ZIP文件所在目录
    """
    if not os.path.isfile(zip_path):
        raise ValueError("指定的路径不是一个有效的文件")

    # 如果没有指定解压路径，则使用zip文件所在的目录
    if extract_to is None:
        extract_to = os.path.splitext(zip_path)[0]  # 以压缩文件名创建文件夹

    # 解压文件
    shutil.unpack_archive(zip_path, extract_to)
    print(f"文件已成功解压至 {extract_to}")
    # extract_zip("./测试压缩/解压目录.zip", "./测试压缩/")

# 加载配置文件
def load_config(file_path="data/config.json"):
    """
    读取 JSON 配置文件的内容。如果文件不存在，则返回 None。
    """
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return None
# 创建配置文件
def create_default_config(file_path="data/config.json", default_config=None):
    """
    创建一个默认的 JSON 配置文件，如果文件不存在。
    可以传递一个默认配置的字典，如果没有提供，则使用预定义的默认配置。
    """
    if default_config is None:
        default_config = {

        }

    # 提取文件目录
    directory = os.path.dirname(file_path)

    # 如果目录不存在，创建目录
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 如果文件不存在，创建文件并写入默认配置
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(default_config, file, indent=4, ensure_ascii=False)
#更新json方法
def update_config_value(key, value, file_path="data/config.json"):
    """
    更新 JSON 配置文件中指定键的值。
    如果文件不存在，自动创建默认配置文件并更新指定值。
    """
    # 读取现有配置
    with open(file_path, 'r', encoding='utf-8') as file:
        config = json.load(file)

    # 更新指定键的值
    config[key] = value

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=4, ensure_ascii=False)
def add_value_to_dict_list(target_dict, key, value):
    """
    向指定字典的值列表中增加值，如果当前值与列表中最后一个值相同，则不添加。
    """
    if key not in target_dict:
        target_dict[key] = []  # 如果键不存在，则创建一个空列表

    # 检查当前值是否与列表中最后一个值相同
    if target_dict[key] and target_dict[key][-1] == value:
        pass
        # print(f"值 '{value}' 已存在，未进行追加。")
    else:
        target_dict[key].append(value)  # 将值添加到列表中
# 追加列表
def updateadd_config_value(key, value, file_path="data/config.json"):

    """
    更新 JSON 配置文件中指定键的值。
    如果文件不存在，自动创建默认配置文件并更新指定值。
    """
    # 检查文件是否存在，如果不存在则创建一个空字典
    if not os.path.isfile(file_path):
        config = {}
    else:
        # 读取现有配置
        with open(file_path, 'r', encoding='utf-8') as file:
            config = json.load(file)

    # 使用辅助函数向指定键的值列表中添加值
    add_value_to_dict_list(config, key, value)

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=4, ensure_ascii=False)
# 删除键
def delete_key_from_json(key,file_path="data/config.json"):
    """
    从指定的 JSON 文件中删除指定的键。

    :param file_path: JSON 文件的路径
    :param key: 要删除的键
    :return: 删除成功则返回 True；若键不存在则返回 False
    """
    if not os.path.exists(file_path):
        print(f"文件 '{file_path}' 不存在。")
        return False

    # 读取 JSON 文件
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 检查并删除键
    if key in data:
        data.pop(key)
        # 写回 JSON 文件
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        print(f"已成功删除键 '{key}'。")
        return True
    else:
        print(f"键 '{key}' 不存在于文件中。")
        return False

# 判断式监控
def monitor_process_if(process_name):
    """
    首次检测到指定名称的进程后，进行 5 秒检测。
    如果 5 秒后进程不再存在，则退出监控。

    :param process_name: 进程的名称
    """
    # print(f"开始监控进程: {process_name}")

    # 检查是否能首次检测到进程
    while True:
        process_found = False
        for process in psutil.process_iter(['name']):
            if process.info['name'] == process_name:
                process_found = True
                break

        # 若首次检测到进程，则等待 5 秒再重新确认
        if process_found:
            pass
            # print(f"检测到进程 {process_name}，开始 5 秒监控...")
            time.sleep(5)

            # 5 秒后再次确认进程是否还在运行
            process_running = False
            for process in psutil.process_iter(['name']):
                if process.info['name'] == process_name:
                    process_running = True
                    break

            if not process_running:
                # print(f"进程 {process_name} 已结束，退出监控。")
                break
        else:
            time.sleep(1)  # 如果未检测到进程，每秒检查一次
# 列出当前游戏进程
def list_visible_app_processes():
    """
    获取当前所有正在运行的应用程序进程名称并返回列表

    :return: 包含所有可见的应用程序进程名称的列表
    """
    app_process_list = []

    for proc in psutil.process_iter(['name', 'pid']):
        try:
            # 检查进程是否有可见窗口
            if proc.info['name'] and proc.info['name'].endswith('.exe'):
                # 只添加可见的进程
                if proc.status() == psutil.STATUS_RUNNING and proc.is_running():
                    if proc.num_handles() > 0:  # 检查是否有句柄，基本上是个简单的判断
                        app_process_list.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return list(set(app_process_list))  # 使用 set 去重

# 选择目录
def select_directory(title):
    # 创建根窗口，但不显示它
    root = tk.Tk()
    root.withdraw()  # 隐藏根窗口

    # 打开目录选择对话框
    selected_directory = filedialog.askdirectory(title=title)

    # 打印选中的目录
    if selected_directory:
        return selected_directory
    else:
        messagebox.showerror('错误','没有选择目录')
        sys.exit(1)  # 终止程序运行并返回状态码1
# 选择zip文件
def select_zip_file(title):
    """
    打开一个文件选择对话框，让用户选择一个 ZIP 文件。

    :param title: 对话框的标题
    :return: 用户选择的 ZIP 文件路径
    """
    # 创建根窗口，但不显示它
    root = tk.Tk()
    root.withdraw()  # 隐藏根窗口

    # 打开文件选择对话框，并限制只选择 ZIP 文件
    selected_file = filedialog.askopenfilename(
        title=title,
        filetypes=[("ZIP 文件", "*.zip")]
    )

    # 返回选中的文件或显示错误消息并退出程序
    if selected_file:
        return selected_file
    else:
        messagebox.showerror('错误', '没有选择 ZIP 文件')
        sys.exit(1)  # 终止程序运行并返回状态码 1

# 选择操作的游戏
def show_keys_from_config(config, callback):
    """
    创建一个顶层窗口来展示字典中的所有键，用户选中后返回该键

    :param config: 字典变量
    :param callback: 选中后调用的回调函数
    """
    def on_select():
        selected_key = listbox.get(tk.ACTIVE)  # 获取选中的键
        callback(selected_key)  # 调用回调函数并传递选中的键
        key_window.destroy()  # 关闭窗口

    # 创建顶层窗口
    key_window = tk.Toplevel()
    key_window.title("选择操作的游戏")

    # 创建列表框并添加字典中的键
    listbox = Listbox(key_window, width=50, height=15)
    listbox.pack(pady=10)

    for key in config.keys():
        listbox.insert(tk.END, key)

    # 创建选择按钮
    select_button = Button(key_window, text="选择", command=on_select)
    select_button.pack(pady=5)

    # 运行顶层窗口的主循环
    key_window.transient(mainmenu)  # 设置为根窗口的临时窗口
    key_window.grab_set()  # 使窗口成为模态窗口

#---运行方法库---
# 添加游戏监控
def Addgame():
    Addgamewindow = tk.Toplevel()
    Addgamewindow.title('添加游戏监控')

    # 初始化环境变量
    process = tk.StringVar()
    notes = tk.StringVar()
    Archivedirectory = tk.StringVar()
    appid = tk.StringVar()

    # 设置游戏存档目录
    def run():
        game_path = select_directory("选择游戏存档目录")
        Archivedirectory.set(game_path)

    # 添加
    def run2():
        update_config_value(notes.get(), [process.get(), Archivedirectory.get(),appid.get()])
        messagebox.showinfo('成功','添加成功')
    # 运行查看所有进程
    def Viewallprocesses():
        subprocess.Popen(["查看所有进程.exe"])
        # subprocess.Popen(['python',"process.py"])

    # 主菜单
    tk.Label(Addgamewindow, text='输入游戏进程：', font=('微软雅黑', 12)).grid(row=1, column=1)
    ttk.Button(Addgamewindow, text='运行查看所有进程', command=Viewallprocesses, padding=(5, 5)).grid(row=1, column=3)
    tk.Entry(Addgamewindow, width=20, font=('微软雅黑', 12), textvariable=process).grid(row=1, column=2)

    tk.Label(Addgamewindow, text='设置游戏备注：', font=('微软雅黑', 12)).grid(row=2, column=1)
    tk.Entry(Addgamewindow, width=20, font=('微软雅黑', 12), textvariable=notes).grid(row=2, column=2)

    tk.Label(Addgamewindow, text='设置游戏存档目录：', font=('微软雅黑', 12)).grid(row=3, column=1)
    tk.Entry(Addgamewindow, width=70, font=('微软雅黑', 12), textvariable=Archivedirectory).grid(row=3, column=2)
    ttk.Button(Addgamewindow, text='更改目录', command=run, padding=(5, 5)).grid(row=3, column=3)

    tk.Label(Addgamewindow, text='输入游戏APPID(可选，不输入则无法进入流程模式)：', font=('微软雅黑', 12)).grid(row=4, column=1)
    tk.Entry(Addgamewindow, width=10, font=('微软雅黑', 12), textvariable=appid).grid(row=4, column=2)

    ttk.Button(Addgamewindow, text='确认添加', command=run2, padding=(10, 5)).grid(row=5, column=1)

# 修改游戏监控
def modifygame():
    config = load_config()
    def handle_selected_key(selected_key):
        modifygamewindow = tk.Toplevel()
        modifygamewindow.title('添加游戏监控')

        # 初始化环境变量
        process = tk.StringVar()
        process.set(config[selected_key][0])
        notes = tk.StringVar()
        notes.set(selected_key)
        Archivedirectory = tk.StringVar()
        Archivedirectory.set(config[selected_key][1])
        appid = tk.StringVar()
        appid.set(config[selected_key][2])

        # 设置游戏存档目录
        def run():
            game_path = select_directory("选择游戏存档目录")
            Archivedirectory.set(game_path)

        # 添加
        def run2():
            update_config_value(notes.get(), [process.get(), Archivedirectory.get(), appid.get()])
            if selected_key != notes.get():
                delete_key_from_json(selected_key)
            messagebox.showinfo('成功', '修改成功')

        # 运行查看所有进程
        def Viewallprocesses():
            subprocess.Popen(["查看所有进程.exe"])
            # subprocess.Popen(['python', "process.py"])

        # 主菜单
        tk.Label(modifygamewindow, text='输入游戏进程：', font=('微软雅黑', 12)).grid(row=1, column=1)
        ttk.Button(modifygamewindow, text='运行查看所有进程', command=Viewallprocesses, padding=(5, 5)).grid(row=1,
                                                                                                          column=3)
        tk.Entry(modifygamewindow, width=20, font=('微软雅黑', 12), textvariable=process).grid(row=1, column=2)

        tk.Label(modifygamewindow, text='设置游戏备注：', font=('微软雅黑', 12)).grid(row=2, column=1)
        tk.Entry(modifygamewindow, width=20, font=('微软雅黑', 12), textvariable=notes).grid(row=2, column=2)

        tk.Label(modifygamewindow, text='设置游戏存档目录：', font=('微软雅黑', 12)).grid(row=3, column=1)
        tk.Entry(modifygamewindow, width=70, font=('微软雅黑', 12), textvariable=Archivedirectory).grid(row=3, column=2)
        ttk.Button(modifygamewindow, text='更改目录', command=run, padding=(5, 5)).grid(row=3, column=3)

        tk.Label(modifygamewindow, text='输入游戏APPID(可选，不输入则无法进入流程模式)：', font=('微软雅黑', 12)).grid(row=4,
                                                                                                                  column=1)
        tk.Entry(modifygamewindow, width=10, font=('微软雅黑', 12), textvariable=appid).grid(row=4, column=2)

        ttk.Button(modifygamewindow, text='确认修改', command=run2, padding=(10, 5)).grid(row=5, column=1)
    show_keys_from_config(config,handle_selected_key)

# 运行游戏监控
def monitor():
    config = load_config()
    def handle_selected_key(selected_key):
        def main():
            but1.config(text='游戏正在运行中',state=tk.DISABLED)
            monitor_process_if(config[selected_key][0])
            but1.config(text='正在备份存档', state=tk.DISABLED)
            nameFile = compress_folder(config[selected_key][1], cache_dir)
            updateadd_config_value(selected_key, nameFile)
            but1.config(text='启动监控', state=tk.NORMAL)
            messagebox.showinfo('完毕','游戏存档已备份')
        thread1 = threading.Thread(target=main)
        thread1.start()
    show_keys_from_config(config,handle_selected_key)

# 恢复存档
def RestoreArchive():
    config = load_config()
    def handle_selected_key(selected_key):
        extract_zip(unzip_dir+'\\'+config[selected_key][3],config[selected_key][1]+'\\')
        messagebox.showinfo('完毕','成功')
    show_keys_from_config(config, handle_selected_key)

# 流程模式
def Process():
    config = load_config()

    #启动
    def start(selected_key):
        but2.config(text='正在覆盖存档', state=tk.DISABLED)
        extract_zip(unzip_dir+'\\'+config[selected_key][3],config[selected_key][1]+'\\')
        os.startfile(f"steam://rungameid/{config[selected_key][2]}")
        monitor(selected_key)
    # 监控
    def monitor(selected_key):
        def main():
            but2.config(text='游戏正在运行中',state=tk.DISABLED)
            monitor_process_if(config[selected_key][0])
            but2.config(text='正在备份存档', state=tk.DISABLED)
            nameFile = compress_folder(config[selected_key][1], cache_dir)
            updateadd_config_value(selected_key, nameFile)
            but2.config(text='启动监控', state=tk.NORMAL)
            messagebox.showinfo('完毕','游戏存档已备份')
        thread1 = threading.Thread(target=main)
        thread1.start()

    show_keys_from_config(config, start)

# 打开存档目录
def Openarchivedirectory():
    os.startfile(unzip_dir)

# 导出所有存档
def allexport():
    File = select_directory('选择导出的位置')
    FileX = File + '\\'+'导出'
    print(File)
    compress_folder(unzip_dir,FileX)
    messagebox.showinfo('成功','导出完毕')
    os.startfile(File)

# 导入存档
def importsave():
    File = select_zip_file('选择导出的文件')
    extract_zip(File,unzip_dir)
    messagebox.showinfo('成功', '导入完毕')
#---主菜单---
global mainmenu
mainmenu = tk.Tk()
mainmenu.geometry("550x300")  # 设置窗口大小
# mainmenu.minsize(450,382)
mainmenu.title('游戏存档自动备份助手1.0')

def WindowEvent():
    os._exit(0)

button_padding = (10, 5)

mainmenu.protocol('WM_DELETE_WINDOW', WindowEvent)

ttk.Button(mainmenu, text='添加游戏监控', command=Addgame, padding=button_padding).place(relx=0.2, y=40, anchor='center')
ttk.Button(mainmenu, text='修改游戏监控', command=modifygame, padding=button_padding).place(relx=0.4, y=40, anchor='center')
ttk.Button(mainmenu, text='删除游戏监控', command='', padding=button_padding).place(relx=0.6, y=40, anchor='center')
ttk.Button(mainmenu, text='导出所有存档', command=allexport, padding=button_padding).place(relx=0.2, y=90, anchor='center')
ttk.Button(mainmenu, text='导入存档', command=importsave, padding=button_padding).place(relx=0.4, y=90, anchor='center')
ttk.Button(mainmenu, text='打开存档目录', command=Openarchivedirectory, padding=button_padding).place(relx=0.6, y=90, anchor='center')

but1 = ttk.Button(mainmenu, text='启动监控', command=monitor, padding=(50, 5))
but1.place(relx=0.5, y=140, anchor='center')
ttk.Button(mainmenu, text='恢复存档', command=RestoreArchive, padding=(50, 5)).place(relx=0.5, y=180, anchor='center')
but2 = ttk.Button(mainmenu, text='流程模式', command=Process, padding=(50, 5))
but2.place(relx=0.5, y=220, anchor='center')

# 开启窗口
mainmenu.mainloop()