import os
from pathlib import Path


def example(data_dir, pattern):
    train_specs = os.listdir(data_dir)
    t_spec_file = data_dir + '/'
    t_spec_file += next(spec for spec in train_specs if pattern in spec)
    return train_specs, Path(t_spec_file)
