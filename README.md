# Board-Climbing-Web-Application

A web-based Kilterboard climbing application that allows users to:

- Generate climbing routes using a Genetic Algorithm (GA)
- Browse climbs from the Kilterboard database
- Save personal climbs with user accounts
- Visualise climbs directly on an interactive board
- Compare generated climbs against real database climbs

---

# Features

## Route Generation
- Generate climbs for specific grades (V1–V10)
- Adjustable wall angle
- Genetic Algorithm based route generation
- Route scoring and fitness evaluation

## Database Climb Search
- Search climbs from the Kilterboard database
- Load climbs directly onto the board visualiser
- Browse climb metadata such as grade and angle

## User Accounts
- Register and login using email
- Save generated climbs
- View saved climbs in the “My Climbs” tab

## Board Visualisation
- Interactive SVG-based Kilterboard rendering
- Colour coded hold roles:
  - Green = Start
  - Cyan = Hand Hold
  - Magenta = Finish
  - Orange = Foot Hold


# Run Application

### Backend Setup

Navigate to backend:

`cd src/backend`

Install dependencies:

`pip install fastapi uvicorn pillow matplotlib numpy`

Run the backend server:

`uvicorn main:app --reload`

### Frontend Setup

Navigate to frontend:

`cd src/frontend`

Install dependencies:

`npm install`

Run the frontend:

`npm run dev`