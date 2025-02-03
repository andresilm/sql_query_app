import torch
from .factory import get_translation_model

translation_model = get_translation_model(torch.cuda.is_available())

