def multiply_matrices(A, B):
    # A and B are 3x3 matrices (lists of lists)
    C = [[0, 0, 0],
         [0, 0, 0],
         [0, 0, 0]]

    for i in range(3):
        for j in range(3):
            for k in range(3):
                C[i][j] += A[i][k] * B[k][j]
    return C

# Example usage:
A = [[1, 2, 3],
     [4, 5, 6],
     [7, 8, 9]]

B = [[9, 8, 7],
     [6, 5, 4],
     [3, 2, 1]]

result = multiply_matrices(A, B)

print("Matrix A:
