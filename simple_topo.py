"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

"""Custom practice"""

from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def build( self ):
        "Create custom topo."

        # Add hosts and switches
        gateway = self.addSwitch( 's1' )

        serv = self.addHost( 'h1' )
        
        device1 = self.addHost( 'h2' )
        device2 = self.addHost( 'h3' )
        device3 = self.addHost( 'h4' )
        device4 = self.addHost( 'h5' )
        
        # Add links
        self.addLink( serv, gateway )
        
        self.addLink( device1, gateway )
        self.addLink( device2, gateway )
        self.addLink( device3, gateway )
        self.addLink( device4, gateway )
        
topos = { 'mytopo': ( lambda: MyTopo() ) }
