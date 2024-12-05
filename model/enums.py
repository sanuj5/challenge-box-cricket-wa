import enum


class InteractiveRequestType(enum.Enum):
    VIEW_BOOKING = "VIEW_BOOKING"
    NEW_BOOKING = "NEW_BOOKING"
    CANCEL_BOOKING = "CANCEL_BOOKING"
    TOURNAMENT_REGISTRATION = "TOURNAMENT_REGISTRATION"


class Day(enum.Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class Month(enum.Enum):
    January = 1
    February = 2
    March = 3
    April = 4
    May = 5
    June = 6
    July = 7
    August = 8
    September = 9
    October = 10
    November = 11
    December = 12


class Slot(enum.Enum):
    S5 = "5 AM- 6 AM"
    S6 = "6 AM- 7 AM"
    S7 = "7 AM- 8 AM"
    S8 = "8 AM- 9 AM"
    S9 = "9 AM- 10 AM"
    S10 = "10 AM- 11 AM"
    S11 = "11 AM- 12 PM"
    S12 = "12 PM- 1 PM"
    S13 = "1 PM- 2 PM"
    S14 = "2 PM- 3 PM"
    S15 = "3 PM- 4 PM"
    S16 = "4 PM- 5 PM"
    S17 = "5 PM- 6 PM"
    S18 = "6 PM- 7 PM"
    S19 = "7 PM- 8 PM"
    S20 = "8 PM- 9 PM"
    S21 = "9 PM- 10 PM"
    S22 = "10 PM- 11 PM"
    S23 = "11 PM- 12 PM"
    S24 = "12 PM- 1 AM"


class Screen(enum.Enum):
    DATE_SELECTION = "DATE_SELECTION"
    SLOT_SELECTION = "SLOT_SELECTION"
    BOOKING_CONFIRMATION = "BOOKING_CONFIRMATION"
    PAYMENT_CONFIRMATION = "PAYMENT_CONFIRMATION"
    SUCCESS = "SUCCESS"
    TOURNAMENT_DETAILS_AND_RULES = "TOURNAMENT_DETAILS_AND_RULES"
    TOURNAMENT_TEAM_REGISTRATION = "TOURNAMENT_TEAM_REGISTRATION"
    TOURNAMENT_BOOKING_CONFIRMATION = "TOURNAMENT_BOOKING_CONFIRMATION"


class MessageType(enum.Enum):
    INTERACTIVE = "interactive"
    TEXT = "text"
    NFM_REPLY = "nfm_reply"
    PAYMENT = "payment"
    NONE = None


class PaymentProvider(enum.Enum):
    PHONEPE = "phone_pe"
    RAZORPAY = "razor_pay"


class Constants(enum.Enum):
    PAYMENT_CONFIGURATION = "cbc_razorpay_20240829"
    TOURNAMENT_REGISTRATION_DETAILS = "Challenge Cricket Academy"
    TOURNAMENT_REGISTRATION_DETAILS2 = """
*** Tournament Details ***

  Tournament Starts from **5 January 2025**

  Winner Prize **₹ 25,000/-**

  Runners up Prize **₹ 11,000/-**

  Entry Fees **₹ 2500/-**
  
*  THE TOURNAMENT WILL BE CHALLENGED ON A KNOCKOUT SYSTEM. *  
  
*** Rules and Regulations ***

** 1. Match rules: **
- 8 overs, 7 players a side
- Team need to report 15 minutes before allotted time.
- Minimum 6 players from each team need to be present to start the match.

** 2. Over per bowler limit: **
- Only 2 bowler can bowl max 2 Overs, rest get to bowl only 1 over.

** 3. Bowling rules: **
- Only standing throw bowling allowed
- Bowling speed will be measured by tracking system. Bowling limit is *75 KMPH* and this limit is subject to change before match based on calibration of tracking system.
- Any ball tracked with speed more than *75 KMPH* will be considered *NO* ball. No warnings will be given.
- Ball Tracking System will be operated by committee member of tournament and results will be available to committee member only. In any circumstances, tracking result or access to system won't be provided to any team.
- If Tracking System is not available for speed tracking due to any technical reason, umpire decision will be considered final for speed limit.

** 4. Batting rules : **
- Fours : Fly through net will be considered as boundary 4 runs
- Sixes : Only direct shot will be considered as boundary 6 runs

** 5. Scoring will be done on the application Cric Heroes. **

** 6. Fielding Rules: **
- First 2 overs will be for batting power play 
- Only 1 player will be allowed in the boundary line for power play
- Wicket keeper is not mandatory
- Catches: Direct catches, no rebounds. For roof rebounds, ball in play but not a catch

** 7. LBW:  **
- No LBW outs, foot deflections may result in leg byes/byes.

** 8. No Ball: **
- No Free Hits will be given in any condition.

** 9. Tie: **
- In case of Tie, Super Over will be played

** 10. Tournament Schedule: **
- Tournament schedule will be finalized before start of tournament. 
- No change in data or time will be possible once the fixure is confirmed. (If you are outside of Anand district, please let us know immediately after registration so we can accommodate your lot for your better convenience)
- Team once gets knocked out of the tournament cannot re-enter.
- A player can play from only one team.

** 11. Final Decision **
- All decisions of the committee of the tournament shall be final and binding on all the participating members. The committee reserves the right to amend the rules at any point of time before/during the tournament in the spirit of the tournament.

** 12. Call +91 9998762618 for any query **    
"""
