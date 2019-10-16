import javax.swing.*;        

public class RouterNode {
  private int myID;
  private GuiTextArea myGUI;
  private RouterSimulator sim;
  private int[] costs = new int[RouterSimulator.NUM_NODES];

  private int[] routes = new int[RouterSimulator.NUM_NODES];
  //private int[][] distTable = new int[RouterSimulator.NUM_NODES][RouterSimulator.NUM_NODES];
  private int[] distVector = new int[RouterSimulator.NUM_NODES];

  private boolean isPoison = true;

  //--------------------------------------------------
  public RouterNode(int ID, RouterSimulator sim, int[] costs) {
    myID = ID;
    this.sim = sim;
    myGUI =new GuiTextArea("  Output window for Router #"+ ID + "  ");

    System.arraycopy(costs, 0, this.costs, 0, RouterSimulator.NUM_NODES);
    //initially, set the distVector equal to costs array
    System.arraycopy(costs, 0, this.distVector, 0, RouterSimulator.NUM_NODES);

    //initialize routes array
    for (int i=0; i < sim.NUM_NODES; i++) {
      if (costs[i]==sim.INFINITY) 
        routes[i] = -1;
      else
        routes[i] = i;
    }

    //send other routers initial distVector
    for (int i=0; i<sim.NUM_NODES; i++) {
      if (i==myID || costs[i]==sim.INFINITY)
          continue;
        sendUpdate(new RouterPacket(myID, i, distVector));
    }

  }

  //--------------------------------------------------
  public void recvUpdate(RouterPacket pkt) {
    boolean changed = false;
    for (int i=0; i<sim.NUM_NODES; i++) {
      //if going through sourceid to node i is less than
      //minimum we know (i.e. distVector[i])
      if (distVector[i] > costs[pkt.sourceid] + pkt.mincost[i]) {
        routes[i] = routes[pkt.sourceid];
        distVector[i] = costs[pkt.sourceid] + pkt.mincost[i];
        changed = true;
      }

      //if we are currently going to node i through source id and if
      //going directly to node i is cheaper than going through sourceid
      if (pkt.sourceid==routes[i] && 
          costs[i] < costs[pkt.sourceid]+pkt.mincost[i]) {
        routes[i] = i;
        distVector[i] = costs[i];
        changed = true;
      }

      //if going from sourceid to node i through this router is cheaper
      //than previously recorded cost from sourceid to node i
      if (!changed && 
          distVector[pkt.sourceid] + distVector[i] < pkt.mincost[i]) {
        sendUpdate(new RouterPacket(myID, i, distVector));
      }
    }

    //if there is change, notify other routers about it
    if (changed) {
      for (int i=0; i<sim.NUM_NODES; i++) {
        if (i==myID || costs[i]==sim.INFINITY)
          continue;
        sendUpdate(new RouterPacket(myID, i, distVector));
      }
    }
  }
  

  //--------------------------------------------------
  private void sendUpdate(RouterPacket pkt) {
    //check if poison reverse in enabled
    if (isPoison) {
      for (int i=0; i<sim.NUM_NODES; i++) {
        //if router goes through destid to reach node i
        //and if node i is not destination node
        if (routes[i] == pkt.destid && i != pkt.destid) {
          myGUI.println("" + i);
          myGUI.println("" + pkt.mincost[i]);
          pkt.mincost[i] = sim.INFINITY;
          myGUI.println("" + pkt.mincost[i]);
        }
      }
    }    
    sim.toLayer2(pkt);
  }
  

  //--------------------------------------------------
  public void printDistanceTable() {
	  myGUI.println("Current table for " + myID +
      "  at time " + sim.getClocktime());

    myGUI.println("");
    
    myGUI.println("Our distance vector and routes: "); 
    myGUI.println("---------------------------------------------------");

    String dst = "dst | \t";
    for (int i=0; i<sim.NUM_NODES; i++) {
      dst += " " + i + "\t";
    }
    myGUI.println(dst);
    myGUI.println("---------------------------------------------------");

    String cost = "cost | \t";
    for (int i=0; i<sim.NUM_NODES; i++) {
      cost += " " + distVector[i] + "\t";
    }
    myGUI.println(cost);

    String route = "route | \t";
    for (int i=0; i<sim.NUM_NODES; i++) {
      route += " " + routes[i] + "\t";
    }
    myGUI.println(route);

    myGUI.println("");
    myGUI.println("");
  }

  //--------------------------------------------------
  public void updateLinkCost(int dest, int newcost) {
    boolean changed = false;
    costs[dest] = newcost;
    //if known mincost to dest is lower than newcost
    //update the mincost
    if (distVector[dest] > newcost) {
      routes[dest] = dest;
      distVector[dest] = newcost;
      changed = true;
    } 
    //if we route through dest node, update the cost to that node
    //even if the newcost is higher than min cost
    else if (dest == routes[dest]) {
      distVector[dest] = newcost;
      changed = true;
    }

    //if there is change, notify other routers about it
    if (changed) {
      for (int i=0; i<sim.NUM_NODES; i++) {
        if (i==myID || costs[i]==sim.INFINITY)
          continue;
        sendUpdate(new RouterPacket(myID, i, distVector));
      }
    }
  }

}
