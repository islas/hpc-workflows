
class SubmitOptions( ) :
  def __init__( self, optDict ) :
    self.submit_ = optDict
    self.working_directory_ = None
    self.queue_             = None
    self.resources_         = None
    self.timelimit_         = None
    self.parse()

  def parse( self ):
    key = "working_directory"
    if key in self.submit_ :
      self.working_directory_ = self.submit_[ key ]
    
    key = "queue"
    if key in self.submit_ :
      self.queue_ = self.submit_[ key ]
    
    key = "resources"
    if key in self.submit_ :
      self.resources_ = self.submit_[ key ]
    
    key = "timelimit"
    if key in self.submit_ :
      self.timelimit_ = self.submit_[ key ]

  def update( self, newOptDict ) :
    self.submit_.update( newOptDict )
    self.parse()
  
  # Check non-optional fields
  def validate( self ) :
    return ( 
            self.queue_ is not None and
            self.resources_ is not None
            )




