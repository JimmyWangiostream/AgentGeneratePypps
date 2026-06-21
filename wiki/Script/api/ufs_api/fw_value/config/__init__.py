import os

config_cwd = os.path.abspath(__file__)[:-len('__init__.py')]
print('[Config path] %s' % (config_cwd,))

config_curr_project = ''  # project module __init__.py中赋值
config_curr_script_name = ''  # script_manager中赋值
config_curr_script_path = ''  # script_manager中赋值

config_lib_root = ''
for _sec in os.path.abspath(__file__).split('scriptlib')[:-1]:  # 初始化lib根目录
    config_lib_root = os.path.join(config_lib_root, _sec)

script_path = os.path.abspath(__file__).split('api')[0]

# config_compiler_debug_info = os.path.join(config_lib_root, 'MpTool\\debug_info.txt')# 初始化debug info的路径
config_compiler_debug_info = os.path.join(script_path, 'project_api','debug_info.txt')# 初始化debug info的路径

# config_c_bin_path = os.path.join(config_lib_root, 'MpTool')
# print(f"config_c_bin_path={config_c_bin_path}")
# for name in os.listdir(config_c_bin_path):
#     if 'FW_C_Header.BIN' in name:
#         config_c_bin_path = os.path.join(config_c_bin_path, name)
#         break

config_log_root = config_lib_root
config_nxs_ip = '10.86.2.113'
