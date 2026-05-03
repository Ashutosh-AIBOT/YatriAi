package com.yatraai.gateway.controller;

import com.yatraai.gateway.dto.PreferenceUpdateRequest;
import com.yatraai.gateway.dto.UserDTO;
import com.yatraai.gateway.exception.ApiResponse;
import com.yatraai.gateway.service.UserService;
import lombok.RequiredArgsConstructor;
import org.slf4j.MDC;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;

    @GetMapping("/me")
    public ApiResponse<UserDTO> getProfile() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        String userId = (String) auth.getPrincipal();
        return ApiResponse.success(userService.getProfile(userId), MDC.get("traceId"));
    }

    @PatchMapping("/preferences")
    public ApiResponse<Void> updatePreferences(@RequestBody PreferenceUpdateRequest request) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        String userId = (String) auth.getPrincipal();
        userService.updatePreferences(userId, request);
        return ApiResponse.success(null, MDC.get("traceId"));
    }
}
