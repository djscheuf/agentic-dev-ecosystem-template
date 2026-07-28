# Administer Tactic Types and Delivery Methods

## Description
As an Administrator, I need to add, remove, turn on or turn off tactic types and their linked delivery method such as mail, mobile app, and in-story kiosk.


## Acceptance Criteria
Given I am an Administrator 
when I am in the section Tactic Type & Delivery Method
Then I see in a list format of tactic types and their linked delivery method
and I can see that they are active or inactive
and I can make them active or inactive
and I can add a new tactic and delivery method.

Function:
Making a Tactic and Method active means that it is now visible to select by requestors in the order form.
Making a Tactic and Method inactive means that it is now not visible to select by requesters and all user types.
Making a Tactic and Method inactive does not remove it from previously ordered/completed requests.  It would still be possible to see this tactic and method in history.

## Tech Note: 
All these requirements are for the Admin Interface only. (tactic-admin)

Delivery Method Specific values:
    Requires Print Support
    Methods are Active or Inactive

Delivery Methods are unique by (Name+ParentType)
CANNOT DELETE, ONLY Mark Inactive

Should ONLY show Tactic Types with At least 1 Method (on the Front End)
Should Have a Drafting mode with explicit Save so people can review the settings. 