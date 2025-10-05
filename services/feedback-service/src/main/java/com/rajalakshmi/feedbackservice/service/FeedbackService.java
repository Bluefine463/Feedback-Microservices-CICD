package com.rajalakshmi.feedbackservice.service;


import com.rajalakshmi.feedbackservice.exception.UnauthorizedException;
import com.rajalakshmi.feedbackservice.model.Feedback;
import com.rajalakshmi.feedbackservice.repository.FeedbackRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Objects;
import java.util.Optional;

@Service
public class FeedbackService {

    @Autowired
    private FeedbackRepository feedbackRepository;

    public Feedback saveFeedback(Feedback feedback) {
        return feedbackRepository.save(feedback);
    }

    public List<Feedback> getAllFeedback() {
        return feedbackRepository.findAll();
    }

    public Optional<Feedback> getFeedbackById(Long id) {
        return feedbackRepository.findById(id);
    }

    public List<Feedback> getFeedbackByUserId(Long userId) {
        return feedbackRepository.findAllByUserId(userId);
    }

    public Feedback updateFeedback(Long id, Feedback feedbackDetails, Long currentUserId, String currentUserRole) {
        Feedback feedback = feedbackRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Feedback not found"));

        if (!Objects.equals(feedback.getUserId(), currentUserId) && !currentUserRole.equals("ADMIN")) {
            throw new UnauthorizedException("User not authorized to update this feedback");
        }

        feedback.setRating(feedbackDetails.getRating());
        feedback.setDescription(feedbackDetails.getDescription());
        return feedbackRepository.save(feedback);
    }

    public void deleteFeedback(Long id, Long currentUserId, String currentUserRole) {
        Feedback feedback = feedbackRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Feedback not found"));

        if (!Objects.equals(feedback.getUserId(), currentUserId) && !currentUserRole.equals("ADMIN")) {
            throw new UnauthorizedException("User not authorized to delete this feedback");
        }
        feedbackRepository.delete(feedback);
    }
}
