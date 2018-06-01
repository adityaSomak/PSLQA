from setuptools import setup, find_packages

setup(name='PSLplus',
      version='0.1',
      description='PSL Python Implementation',
      url='https://gitlab.com/somakaditya/pslqa-backup',
      author='Somak Aditya',
      author_email='saditya1@asu.edu',
      license='MIT',
      packages=find_packages(),
      install_requires=['numpy','gurobipy'],
      zip_safe=False)