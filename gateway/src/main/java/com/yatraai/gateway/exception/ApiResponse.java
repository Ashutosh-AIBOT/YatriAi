package com.yatraai.gateway.exception;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ApiResponse<T> {
    private boolean success;
    private T data;
    private ErrorDetail error;
    private String traceId;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ErrorDetail {
        private int code;
        private String message;
    }

    public static <T> ApiResponse<T> success(T data, String traceId) {
        return ApiResponse.<T>builder()
                .success(true)
                .data(data)
                .traceId(traceId)
                .build();
    }

    public static <T> ApiResponse<T> error(int code, String message, String traceId) {
        return ApiResponse.<T>builder()
                .success(false)
                .error(new ErrorDetail(code, message))
                .traceId(traceId)
                .build();
    }
}
