#include <metal_stdlib>

using namespace metal;

kernel void cos_func(device float* in [[buffer(0)]], device float* out [[buffer(1)]], uint id  [[thread_position_in_grid]]) {
    out[id] = cos(in[id]);
};

kernel void adder(device int* arr1 [[buffer(0)]], device int* arr2 [[buffer(1)]], device int* arr3 [[buffer(2)]], uint id [[thread_position_in_grid]]) {
    arr3[id] = arr2[id] + arr1[id];
};

