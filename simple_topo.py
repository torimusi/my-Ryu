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
        gateway = self.addSwitch( 'g1' )

        serv = self.addHost(' sv ')
        
        device1 = self.addHost( 'd1' )
        device2 = self.addHost( 'd2' )
        device3 = self.addHost( 'd3' )
        device4 = self.addHost( 'd4' )
        
        # Add links
        self.addLink( gateway, serv )
        
        self.addLink( device1, serv )
        self.addLink( device2, serv )
        self.addLink( device3, serv )
        self.addLink( device4, serv )
        
topos = { 'mytopo': ( lambda: MyTopo() ) }
