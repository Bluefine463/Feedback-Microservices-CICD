package com.rajalakshmi.feedbackservice.controller;


import com.rajalakshmi.feedbackservice.exception.UnauthorizedException;
import com.rajalakshmi.feedbackservice.model.Feedback;
import com.rajalakshmi.feedbackservice.service.FeedbackService;
import com.rajalakshmi.feedbackservice.service.FileStorageService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.util.List;

@RestController
@RequestMapping("/feedback")
public class FeedbackController {

    @Autowired
    private FeedbackService feedbackService;

    @Autowired
    private FileStorageService fileStorageService;

    @PostMapping(consumes = {"multipart/form-data"})
    public ResponseEntity<Feedback> createFeedback(@RequestParam("rating") int rating,
                                                   @RequestParam("description") String description,
                                                   @RequestHeader("X-User-Id") Long userId,
                                                   @RequestParam(value = "image", required = false) MultipartFile image) {
        Feedback feedback = new Feedback();
        feedback.setUserId(userId);
        feedback.setRating(rating);
        feedback.setDescription(description);

        if (image != null && !image.isEmpty()) {
            String fileName = fileStorageService.storeFile(image);
            String fileDownloadUri = ServletUriComponentsBuilder.fromCurrentContextPath()
                    .path("/feedback/uploads/")
                    .path(fileName)
                    .toUriString();
            feedback.setImageUrl(fileDownloadUri);
        }

        Feedback savedFeedback = feedbackService.saveFeedback(feedback);
        return new ResponseEntity<>(savedFeedback, HttpStatus.CREATED);
    }

    @GetMapping
    public ResponseEntity<List<Feedback>> getAllFeedback(@RequestHeader("X-User-Role") String userRole) {
        // Check if the user is an ADMIN
        if (!"ADMIN".equalsIgnoreCase(userRole)) {
            return new ResponseEntity<>(HttpStatus.FORBIDDEN); // Return 403 if not an admin
        }
        List<Feedback> feedbackList = feedbackService.getAllFeedback();
        return new ResponseEntity<>(feedbackList, HttpStatus.OK);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Feedback> getFeedbackById(@PathVariable Long id) {
        return feedbackService.getFeedbackById(id)
                .map(feedback -> new ResponseEntity<>(feedback, HttpStatus.OK))
                .orElse(new ResponseEntity<>(HttpStatus.NOT_FOUND));
    }

    @GetMapping("/user/{userId}")
    public ResponseEntity<List<Feedback>> getFeedbackByUserId(@PathVariable Long userId) {
        List<Feedback> userFeedbackList = feedbackService.getFeedbackByUserId(userId);
        return new ResponseEntity<>(userFeedbackList, HttpStatus.OK);
    }

    @GetMapping("/uploads/{filename:.+}")
    @ResponseBody
    public ResponseEntity<Resource> serveFile(@PathVariable String filename) {
        Resource file = fileStorageService.loadFileAsResource(filename);
        return ResponseEntity.ok().header(HttpHeaders.CONTENT_DISPOSITION,
                "inline; filename=\"" + file.getFilename() + "\"").body(file);
    }

    @PutMapping("/{id}")
    public ResponseEntity<Feedback> updateFeedback(@PathVariable Long id,
                                                   @RequestBody Feedback feedbackDetails,
                                                   @RequestHeader("X-User-Id") Long userId,
                                                   @RequestHeader("X-User-Role") String userRole) {
        try {
            Feedback updatedFeedback = feedbackService.updateFeedback(id, feedbackDetails, userId, userRole);
            return new ResponseEntity<>(updatedFeedback, HttpStatus.OK);
        } catch (UnauthorizedException e) {
            return new ResponseEntity<>(HttpStatus.FORBIDDEN);
        } catch (RuntimeException e) {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<HttpStatus> deleteFeedback(@PathVariable Long id,
                                                     @RequestHeader("X-User-Id") Long userId,
                                                     @RequestHeader("X-User-Role") String userRole) {
        try {
            feedbackService.deleteFeedback(id, userId, userRole);
            return new ResponseEntity<>(HttpStatus.NO_CONTENT);
        } catch (UnauthorizedException e) {
            return new ResponseEntity<>(HttpStatus.FORBIDDEN);
        } catch (RuntimeException e) {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }
    }
}