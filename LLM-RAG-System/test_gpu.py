# test_gpu.py dosyası oluşturup içine aşağıdaki kodu yazın
import torch
print(f"CUDA kullanılabilir: {torch.cuda.is_available()}")
print(f"CUDA cihaz sayısı: {torch.cuda.device_count()}")
print(f"CUDA cihaz adı: {torch.cuda.get_device_name(0)}")