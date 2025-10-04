package com.rajalakshmi.userservice.service;

import com.rajalakshmi.userservice.model.User;
import com.rajalakshmi.userservice.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Optional;

@Component
public class UserDetailsServiceImpl implements UserDetailsService {

    @Autowired
    private UserRepository repository;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        Optional<User> user = repository.findByUsername(username);
        return user.map(UserInfoDetails::new)
                .orElseThrow(() -> new UsernameNotFoundException("User not found " + username));
    }

    public static class UserInfoDetails extends org.springframework.security.core.userdetails.User {
        public UserInfoDetails(User user) {
            super(user.getUsername(), user.getPassword(), List.of(() -> "ROLE_" + user.getRole().name()));
        }
    }
}