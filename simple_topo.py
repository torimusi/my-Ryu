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
        host1 = self.addHost( 'h1' )
        host2 = self.addHost( 'h2' )
        host3 = self.addHost( 'h3' )
        host4 = self.addHost( 'h4' )
        host5 = self.addHost( 'h5' )
        host6 = self.addHost( 'h6' )
        serv = self.addHost(' sv ')
        
        Switch1 = self.addSwitch( 's1' )
        Switch2 = self.addSwitch( 's2' )
        Switch3 = self.addSwitch( 's3' )

        # Add links
        self.addLink( host1, Switch1 )
        self.addLink( host2, Switch1 )
        self.addLink( host3, Switch1 )

        self.addLink( host4, Switch2 )
        self.addLink( host5, Switch2 )
        self.addLink( host6, Switch2 )
        
        self.addLink( Switch1, Switch2 )
        self.addLink( Switch2, Switch3 )
        self.addLink( Switch3, Switch1 )

        self.addLink( Switch3, serv )
        
topos = { 'mytopo': ( lambda: MyTopo() ) }
