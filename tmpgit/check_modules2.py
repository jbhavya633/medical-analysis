try:
    import torch
    print('torch', torch.__version__)
except:
    print('no torch')

try:
    import tensorflow
    print('tensorflow', tensorflow.__version__)
except:
    print('no tensorflow')

try:
    import keras
    print('keras', keras.__version__)
except:
    print('no keras')

try:
    import sklearn
    print('sklearn', sklearn.__version__)
except:
    print('no sklearn')
