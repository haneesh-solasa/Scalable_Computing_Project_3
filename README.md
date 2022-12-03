**Scalable - Computing Project 3 : Satellite Based Ship Safety prediction using NDN (Name Data Networking)**

**Every process should be run on seperate Pis**

Step 1: Run the Satellite.py `python3 Satellite.py` to start training the model, the program waits for the user to input. The user has to wait until the router is started and the training is complete. When the training is done, the satellite will print out a "waiting..." message, at which point any key press will activate it. It's best to activate the satellite after all 4 buoys are started, but that's not required.

Step 2: Run Router.py `python3 router.py --name router1` to start listening to the broadcasts.

Step 3: Run all 4 buoys on separate PIs 

`python3 buoy.py --name A1` 

`python3 buoy.py --name A2` 

`python3 buoy.py --name B1`

`python3 buoy.py --name B2`

Step 4: Run the ship.py `python3 Ship.py --name ship1 --loc B1` and it automatically sends the interest to the Satellite every 10 seconds (simulation - 1 hr). 


The satellite predicts the weather for the next 5 hrs and returns the best location the ship needs to be. This will be printed in the ship window, as either moving to: or staying in: and the location.

## Code contributions
Adam Ogórek - Router

Teona Banu - Weather Forecast Model and gathered weather data

Haneesh Solasa - Satellite

Vipul Ghare - Buoy and ship
