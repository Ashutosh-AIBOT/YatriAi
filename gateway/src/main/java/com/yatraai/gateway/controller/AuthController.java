package com.yatraai.gateway.controller;

import com.yatraai.gateway.dto.LoginRequest;
import com.yatraai.gateway.dto.RegisterRequest;
import com.yatraai.gateway.exception.ApiResponse;
import com.yatraai.gateway.service.AuthService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.slf4j.MDC;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {
    private final AuthService authService;

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    public ApiResponse<Map<String, Object>> register(@Valid @RequestBody RegisterRequest request) {
        return ApiResponse.success(authService.register(request), MDC.get("traceId"));
    }

    @PostMapping("/login")
    public ApiResponse<Map<String, String>> login(@Valid @RequestBody LoginRequest request) {
        return ApiResponse.success(authService.login(request), MDC.get("traceId"));
    }
}
