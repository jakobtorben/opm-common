These ML modules are extending the previous work done in Kerasify by Maevskikh and Rose licensed under the terms of the MIT 
license (https://github.com/moof2k/kerasify/tree/77a0c42). Kerasify is a library for running trained Keras models from a C++ platform.
Our implementation is also compliant with the automatic differentiation approach used in OPM.
The implementation works with Python v.3.9.0 and above (up to <=3.12.0).

-Unit tests are generated by:

$ python3 generateunittests.py


-To compile run the unit tests:
 
$ make ml_model_test
$ ./bin/ml_model_test
TEST tensor_test
TEST dense_1x1
TEST dense_10x1
TEST dense_2x2
TEST dense_10x10
TEST dense_10x10x10
TEST relu_10
TEST dense_relu_10
TEST dense_tanh_10
TEST scalingdense_10x1