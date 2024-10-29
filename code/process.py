import tkinter as tk
from tkinter import Listbox, Entry, Button
import psutil

def list_visible_app_processes():
    """
    获取当前所有正在运行的应用程序进程名称并返回列表
    """
    app_process_list = []
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].endswith('.exe'):
                app_process_list.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return list(set(app_process_list))

def search_processes():
    """根据搜索框内容过滤进程列表"""
    query = search_entry.get().lower()
    listbox.delete(0, tk.END)  # 清空列表框
    for process in all_processes:
        if query in process.lower():
            listbox.insert(tk.END, process)

def copy_selected_process():
    """复制选中的进程名称到剪贴板"""
    selected_process = listbox.get(tk.ACTIVE)
    root.clipboard_clear()  # 清空剪贴板
    root.clipboard_append(selected_process)  # 添加选中的进程名称到剪贴板
    print(f"复制到剪贴板: {selected_process}")

# 创建主窗口
root = tk.Tk()
root.title("应用进程列表")

# 获取运行的应用程序进程
all_processes = list_visible_app_processes()

# 创建搜索框
search_entry = Entry(root, width=50)
search_entry.grid(row=0, column=0)
search_entry.bind("<KeyRelease>", lambda event: search_processes())  # 绑定按键释放事件

# 创建列表框并添加进程
listbox = Listbox(root, width=50, height=15)
listbox.grid(row=1, column=0)

# 将进程添加到列表框中
for process in all_processes:
    listbox.insert(tk.END, process)

# 创建复制按钮
copy_button = Button(root, text="复制选中进程", command=copy_selected_process)
copy_button.grid(row=2, column=0)

# 运行主循环
root.mainloop()
