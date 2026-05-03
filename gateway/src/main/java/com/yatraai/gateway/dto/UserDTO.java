package com.yatraai.gateway.dto;

import lombok.Builder;
import lombok.Data;

import java.time.OffsetDateTime;
import java.util.UUID;

@Data
@Builder
public class UserDTO {
    private UUID id;
    private String name;
    private String email;
    private String language;
    private Boolean isActive;
    private OffsetDateTime createdAt;
}
