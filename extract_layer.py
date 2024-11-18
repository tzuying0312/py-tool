import tarfile
import os

def extract_layer(layer_tar_path, output_dir):
    """解壓單個 layer.tar 檔案到指定資料夾"""
    if not os.path.exists(layer_tar_path):
        print(f"警告: {layer_tar_path} 不存在，跳過解壓。")
        return

    with tarfile.open(layer_tar_path, 'r') as layer_tar:
        # 生成解壓的資料夾
        layer_data_dir = os.path.splitext(layer_tar_path)[0]
        os.makedirs(layer_data_dir, exist_ok=True)
        
        # 解壓到該資料夾
        print(f'正在解壓縮 {layer_tar_path} 到 {layer_data_dir}')
        layer_tar.extractall(layer_data_dir)
    
    # 刪除 layer.tar 檔案（選擇性）
    os.remove(layer_tar_path)

def extract_docker_image(docker_image_tar, output_dir):
    """解壓 Docker 映像檔並處理所有層"""
    with tarfile.open(docker_image_tar, 'r') as tar:
        # 確保輸出目錄存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 獲取 tar 包中的所有檔案
        members = tar.getmembers()
        
        # 找出所有包含 'layer.tar' 的檔案
        layer_folders = [m for m in members if m.name.endswith('layer.tar')]
        
        # 如果 layer.tar 不存在
        if not layer_folders:
            print("警告: 沒有發現 layer.tar 檔案！")
            return
        
        for layer_folder in layer_folders:
            # 根據層的資料夾結構創建目標路徑
            layer_path = os.path.dirname(layer_folder.name)  # 包含 layer.tar 的資料夾
            layer_extract_dir = os.path.join(output_dir, layer_path)
            
            # 創建該層資料夾
            os.makedirs(layer_extract_dir, exist_ok=True)
            
            # 提取 layer.tar 到對應的資料夾中
            print(f'正在提取 {layer_folder.name} 到 {layer_extract_dir}')
            tar.extract(layer_folder, layer_extract_dir)
            
            # 解壓該層的 layer.tar
            layer_tar_path = os.path.join(layer_extract_dir, os.path.basename(layer_folder.name))
            extract_layer(layer_tar_path, layer_extract_dir)

        print("所有層已解壓完畢。")

# 使用範例
file='test'
docker_image_tar = file+'.tar'  # Docker save 生成的 tar 檔案路徑
output_dir = './'+file   # 解壓後的目標資料夾

extract_docker_image(docker_image_tar, output_dir)
