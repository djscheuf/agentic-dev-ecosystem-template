# Create New Tactics

## Description

So that I can start capaturing a new Digital Tactic
As an Internal Requester
I want to be able to request a new tactic, selecting fixed info ( like Tactic Type) from a list, and to have the system validate my selections
AND to be able to edit the tactic before sending it to Proof-readers

See Attached New Tactic View for Prototype of Page AFTER Story Complete

## Acceptance Criteria

### Request New Digital Tactic 

Given I am a registered Internal Requester 

AND I provide the required minimum Tactic Info (Owner (default to user ID), Tactic Type, Start Date, Title) 

When I submit a new Tactic 

THEN my tactic is assigned a unique Id 

AND my tactic is captured in DRAFT status 

 

### Request New Digital Tactic W/ Alt Owner 

Given I am a registered Internal Requester 

AND I provide the required minimum Tactic Info (Owner (user provided), Tactic Type, Start Date, Title) 

And I provide an alternative Internal OWNER 

When I submit a new Tactic 

THEN my tactic is assigned a unique Id 

AND my tactic is captured in DRAFT status 

AND that OWNER is Assigned as Current Owner 

AND I AM logged as the Requester 

 

### Missing Minimum Information 

Given I am a registered Internal Requester 

AND I do NOT provide ALL the required minimum Tactic Info (Tactic Type, or Start Date, or Title) 

When I ATTEMPT submit a new Tactic 

THEN my tactic is NOT assigned a unique Id 

AND my tactic is NOT captured in DRAFT status 

AND I receive a relevant warning message regarding the missing information 

## Technical Notes
### Tactic Types We Need
Title for this is Tactic Distribution Method
CouponMachine
InternetPrintout
MobileCoupon
