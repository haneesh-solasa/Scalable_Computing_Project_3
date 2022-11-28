**Scalable - Computing Project 3 : Satellite Based Ship Safety prediction using NDN (Name Data Networking)**

**Every process should be run on seperate Pis**

Step 1: Run the Satellite.py to start training the model, the program waits for the user to input. The user has to wait until the router is started and the training is complete.
Step 2: Run Router.py to start listening to the broadcasts.
Step 3: Run the buoy.py with all the four arguments (A1, A2, B1, B2)
Step 4: Run the ship.py and it automatically sends the interest to the Satellite every 10 seconds (simulation - 1 hr). 

The satellite predicts the weather for the next 5 hrs and returns the best location the ship needs to be.
