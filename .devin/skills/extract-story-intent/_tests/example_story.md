# Simple Calculator

## Description

So that I can perform basic addition operations
As a user
I want to be able to add two positive integers together

## Acceptance Criteria

### Add Two Positive Integers

Given I am a user

AND I provide two positive integers

When I submit the addition request

THEN the system returns the sum of the two integers

### Add Negative Numbers

Given I am a user

AND I provide one negative integer and one positive integer

When I submit the addition request

THEN the system returns an error message

### Add Zero

Given I am a user

AND I provide one zero and one positive integer

When I submit the addition request

THEN the system returns the positive integer

## Technical Notes
- Input validation for positive integers
- Error handling for negative numbers needs to keep app running, while informing user of error. 
- App should be simple, with terminal interface for now. 
- Probably use javascript for now to keep it simple. 
- Design for extensibility to support more arithmetic operations in the future.
