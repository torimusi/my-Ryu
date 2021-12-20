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
        gateway1 = self.addSwitch( 'g1' )
        gateway2 = self.addSwitch( 'g2' )

        serv = self.addHost(' sv ')
        
        Switch = self.addSwitch( 's1' )
        
        # Add links
        self.addLink( gateway1, Switch )
        self.addLink( gateway2, Switch )
        
        self.addLink( Switch, serv )
        
topos = { 'mytopo': ( lambda: MyTopo() ) }
