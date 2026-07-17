#include <cuda_runtime.h>

#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <vector>

#define CUDA_CHECK(call)                                                        \
    do {                                                                        \
        cudaError_t status_ = (call);                                           \
        if (status_ != cudaSuccess) {                                           \
            std::cerr << "cuda_error=" << cudaGetErrorString(status_)          \
                      << " line=" << __LINE__ << '\n';                         \
            return EXIT_FAILURE;                                                \
        }                                                                       \
    } while (false)

__global__ void affine(const float* input, float* output, std::size_t count) {
    const std::size_t index = blockIdx.x * blockDim.x + threadIdx.x;
    if (index < count) {
        output[index] = 2.0F * input[index] + 1.0F;
    }
}

int main() {
    int device_count = 0;
    CUDA_CHECK(cudaGetDeviceCount(&device_count));
    if (device_count != 1) {
        std::cerr << "expected_device_count=1 actual=" << device_count << '\n';
        return EXIT_FAILURE;
    }

    cudaDeviceProp properties{};
    CUDA_CHECK(cudaGetDeviceProperties(&properties, 0));
    std::cout << "device_count=" << device_count << '\n'
              << "device_name=" << properties.name << '\n'
              << "compute_capability=" << properties.major << '.'
              << properties.minor << '\n';

    constexpr std::size_t count = 1U << 20U;
    constexpr std::size_t bytes = count * sizeof(float);
    std::vector<float> input(count);
    std::vector<float> output(count, 0.0F);
    for (std::size_t index = 0; index < count; ++index) {
        input[index] = static_cast<float>(index % 4096U) / 1024.0F;
    }

    float* device_input = nullptr;
    float* device_output = nullptr;
    CUDA_CHECK(cudaMalloc(&device_input, bytes));
    CUDA_CHECK(cudaMalloc(&device_output, bytes));
    CUDA_CHECK(cudaMemcpy(device_input, input.data(), bytes,
                          cudaMemcpyHostToDevice));

    constexpr unsigned threads = 256;
    const unsigned blocks = static_cast<unsigned>((count + threads - 1) / threads);
    affine<<<blocks, threads>>>(device_input, device_output, count);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());
    CUDA_CHECK(cudaMemcpy(output.data(), device_output, bytes,
                          cudaMemcpyDeviceToHost));

    double checksum = 0.0;
    float max_error = 0.0F;
    for (std::size_t index = 0; index < count; ++index) {
        const float expected = 2.0F * input[index] + 1.0F;
        max_error = std::fmax(max_error, std::fabs(output[index] - expected));
        checksum += static_cast<double>(output[index]);
    }

    CUDA_CHECK(cudaFree(device_output));
    CUDA_CHECK(cudaFree(device_input));
    if (max_error != 0.0F || !std::isfinite(checksum)) {
        std::cerr << "numeric_check=fail max_error=" << max_error << '\n';
        return EXIT_FAILURE;
    }

    std::cout << std::setprecision(17) << "element_count=" << count << '\n'
              << "checksum=" << checksum << '\n'
              << "max_error=" << max_error << '\n'
              << "cuda_smoke=pass\n";
    return EXIT_SUCCESS;
}
