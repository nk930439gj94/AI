# multiAgents.py
# --------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from util import manhattanDistance
from game import Directions
import random, util
import searchAgents

from game import Agent

class ReflexAgent(Agent):
	"""
		A reflex agent chooses an action at each choice point by examining
		its alternatives via a state evaluation function.

		The code below is provided as a guide.  You are welcome to change
		it in any way you see fit, so long as you don't touch our method
		headers.
	"""


	def getAction(self, gameState):
		"""
		You do not need to change this method, but you're welcome to.

		getAction chooses among the best options according to the evaluation function.

		Just like in the previous project, getAction takes a GameState and returns
		some Directions.X for some X in the set {North, South, West, East, Stop}
		"""
		# Collect legal moves and successor states
		legalMoves = gameState.getLegalActions()

		# Choose one of the best actions
		scores = [self.evaluationFunction(gameState, action) for action in legalMoves]
		bestScore = max(scores)
		bestIndices = [index for index in range(len(scores)) if scores[index] == bestScore]
		chosenIndex = random.choice(bestIndices) # Pick randomly among the best

		"Add more of your code here if you want to"

		return legalMoves[chosenIndex]

	def evaluationFunction(self, currentGameState, action):
		"""
		Design a better evaluation function here.

		The evaluation function takes in the current and proposed successor
		GameStates (pacman.py) and returns a number, where higher numbers are better.

		The code below extracts some useful information from the state, like the
		remaining food (newFood) and Pacman position after moving (newPos).
		newScaredTimes holds the number of moves that each ghost will remain
		scared because of Pacman having eaten a power pellet.

		Print out these variables to see what you're getting, then combine them
		to create a masterful evaluation function.
		"""
		# Useful information you can extract from a GameState (pacman.py)
		successorGameState = currentGameState.generatePacmanSuccessor(action)
		newPos = successorGameState.getPacmanPosition()
		newFood = successorGameState.getFood()
		newGhostStates = successorGameState.getGhostStates()
		newScaredTimes = [ghostState.scaredTimer for ghostState in newGhostStates]

		"*** YOUR CODE HERE ***"
		import random
		newFoodList = newFood.asList()
		if not newFoodList:
			dist_greedyeat=0
		else:
			dist_greedyeat=min([ util.manhattanDistance(newPos,i) for i in newFoodList ])
		nearghost,dist_chase=0,0
		for i in range( len(newGhostStates) ):
			dist_ptoghost = util.manhattanDistance(newPos,newGhostStates[i].getPosition())
			if newScaredTimes[i] > dist_ptoghost:
				dist_chase+=dist_ptoghost
			else:
				dist_ghost=util.manhattanDistance(newPos,newGhostStates[i].getPosition())
				if dist_ghost < 3:
					nearghost+=3-dist_ghost
		return -50*len(newFoodList)-dist_greedyeat-10*dist_chase-100*nearghost+random.randint(0,2)

def scoreEvaluationFunction(currentGameState):
	"""
		This default evaluation function just returns the score of the state.
		The score is the same one displayed in the Pacman GUI.

		This evaluation function is meant for use with adversarial search agents
		(not reflex agents).
	"""
	return currentGameState.getScore()

class MultiAgentSearchAgent(Agent):
	"""
		This class provides some common elements to all of your
		multi-agent searchers.  Any methods defined here will be available
		to the MinimaxPacmanAgent, AlphaBetaPacmanAgent & ExpectimaxPacmanAgent.

		You *do not* need to make any changes here, but you can if you want to
		add functionality to all your adversarial search agents.  Please do not
		remove anything, however.

		Note: this is an abstract class: one that should not be instantiated.  It's
		only partially specified, and designed to be extended.  Agent (game.py)
		is another abstract class.
	"""

	def __init__(self, evalFn = 'scoreEvaluationFunction', depth = '2'):
		self.index = 0 # Pacman is always agent index 0
		self.evaluationFunction = util.lookup(evalFn, globals())
		self.depth = int(depth)

class MinimaxAgent(MultiAgentSearchAgent):
	"""
		Your minimax agent (question 2)
	"""

	def getAction(self, gameState):
		"""
			Returns the minimax action from the current gameState using self.depth
			and self.evaluationFunction.

			Here are some method calls that might be useful when implementing minimax.

			gameState.getLegalActions(agentIndex):
			Returns a list of legal actions for an agent
			agentIndex=0 means Pacman, ghosts are >= 1

			gameState.generateSuccessor(agentIndex, action):
			Returns the successor game state after an agent takes an action

			gameState.getNumAgents():
			Returns the total number of agents in the game
		"""
		"*** YOUR CODE HERE ***"
		l=[]
		for i in gameState.getLegalActions(0):
			l.append( ( self._myminimax(gameState.generateSuccessor(0,i),1,1), i ) )
		return max(l)[1]
		

	def _myminimax(self,gameState,agentIndex,depth):
		if gameState.isWin() or gameState.isLose() or depth>self.depth:
			return self.evaluationFunction(gameState)
		l=[]
		newagentIndex,newdepth=agentIndex+1,depth
		fn=min
		if newagentIndex==gameState.getNumAgents():
			newagentIndex=0
			newdepth+=1
		if agentIndex==0:
			fn=max
		for i in gameState.getLegalActions(agentIndex):
			l.append( self._myminimax(gameState.generateSuccessor(agentIndex,i),newagentIndex,newdepth) )
		return fn(l)
			

		

class AlphaBetaAgent(MultiAgentSearchAgent):
	"""
		Your minimax agent with alpha-beta pruning (question 3)
	"""

	def getAction(self, gameState):
		"""
			Returns the minimax action using self.depth and self.evaluationFunction
		"""
		"*** YOUR CODE HERE ***"
		v = (-9999999,Directions.STOP)
		alpha,beta=-9999999,9999999
		for i in gameState.getLegalActions(0):
			v=max( v, ( self._myalphabeta(gameState.generateSuccessor(0,i),1,1,alpha,beta), i ) )
			alpha=max(alpha,v[0])
		return v[1]
		


	def _myalphabeta(self,gameState,agentIndex,depth,alpha,beta):
		newalpha,newbeta = int(alpha), int(beta)
		if gameState.isWin() or gameState.isLose() or depth>self.depth:
			return self.evaluationFunction(gameState)
		newagentIndex,newdepth=agentIndex+1,depth
		if newagentIndex==gameState.getNumAgents():
			newagentIndex=0
			newdepth+=1
		if agentIndex==0:
			v=-9999999
			for i in gameState.getLegalActions(agentIndex):
				v=max( v, self._myalphabeta(gameState.generateSuccessor(agentIndex,i),newagentIndex,newdepth,newalpha,newbeta) )
				if v>=newbeta: return v
				newalpha=max(newalpha,v)
		else:
			v=9999999
			for i in gameState.getLegalActions(agentIndex):
				v=min( v, self._myalphabeta(gameState.generateSuccessor(agentIndex,i),newagentIndex,newdepth,newalpha,newbeta) )
				if v<=newalpha: return v
				newbeta=min(newbeta,v)
		return v

class ExpectimaxAgent(MultiAgentSearchAgent):
	"""
		Your expectimax agent (question 4)
	"""

	def getAction(self, gameState):
		"""
			Returns the expectimax action using self.depth and self.evaluationFunction

			All ghosts should be modeled as choosing uniformly at random from their
			legal moves.
		"""
		"*** YOUR CODE HERE ***"
		l=[]
		for i in gameState.getLegalActions(0):
			l.append( ( self._myexpextmax(gameState.generateSuccessor(0,i),1,1), i ) )
		return max(l)[1]
		

	def _myexpextmax(self,gameState,agentIndex,depth):
		if gameState.isWin() or gameState.isLose() or depth>self.depth:
			return self.evaluationFunction(gameState)
		l=[]
		newagentIndex,newdepth=agentIndex+1,depth
		if newagentIndex==gameState.getNumAgents():
			newagentIndex=0
			newdepth+=1
		for i in gameState.getLegalActions(agentIndex):
			l.append( self._myexpextmax(gameState.generateSuccessor(agentIndex,i),newagentIndex,newdepth) )
		if agentIndex==0:
			return max(l)
		else:
			return float(sum(l))/len(l)


		


def betterEvaluationFunction(currentGameState):
	"""
		Your extreme ghost-hunting, pellet-nabbing, food-gobbling, unstoppable
		evaluation function (question 5).

		DESCRIPTION: <write something here so we know what you did>
	"""
	"*** YOUR CODE HERE ***"
	import random

	position = currentGameState.getPacmanPosition()
	foodlist = currentGameState.getFood().asList()
	GhostStates = currentGameState.getGhostStates()
	capsulelist = currentGameState.getCapsules()

	
	if not foodlist:
		dist_greedyeat=0
	else:
		dist_greedyeat=min([ util.manhattanDistance(position,i) for i in foodlist ])
	eatingfood =-50*len(foodlist)-dist_greedyeat+random.randint(0,2)


	if not capsulelist:
		dist_greedycapsule=0
	else:
		dist_greedycapsule=min([ util.manhattanDistance(position,i) for i in capsulelist ])
	eatingcapsule = -50*len(capsulelist)-dist_greedycapsule
	ischasing=False
	for i in GhostStates:
		if i.scaredTimer>util.manhattanDistance(position,i.getPosition()):
			ischasing=True
			break
	if ischasing and len(capsulelist)==1 :
		eatingcapsule+=2


	nearghost,dist_chase=0,0
	for i in GhostStates:
		dist_ghost = util.manhattanDistance(position,i.getPosition())
		if i.scaredTimer > dist_ghost:
			dist_chase+=dist_ghost
		elif dist_ghost < 2:
			nearghost+=(2-dist_ghost)
	ghostchase = -dist_chase-5*nearghost


	specialcase=0
	deadzone = [ (9,5), (12,5), (10,5), (11,5) ]
	if position in deadzone:
		specialcase-=1
	if position in deadzone[:2]:
		specialcase-=1

	islosing=0
	if currentGameState.isLose():
		islosing=1
	
	return eatingfood+40*eatingcapsule+100*ghostchase+99999*specialcase-9999999*islosing


# Abbreviation
better = betterEvaluationFunction

