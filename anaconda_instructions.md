# Fixa anaconda environment för BrainFlow i Python

## Ladda ner anaconda (om du inte redan har det)
 - Följ instruktionerna för installation i ditt operativsystem på [docs.anaconda.com](https://docs.anaconda.com/anaconda/install/).

## Skapa en ny envionment
 - `conda create --name braingame` och svara ja om du vill spara environment på default location.
 - `conda activate braingame`
 

## Lägg till biblioteket BrainFlow i conda-miljön

 - Installera pip i din environment: `conda install pip` 
 - Kör `which pip` (linux/macOS) eller `where pip` (windows) för att verifiera att när kommandot `pip` körs, så används den versionen av pip som är installerad i conda-miljön `braingame`. E.g.:
```bash
(braingame) elias@xps13:~/Documents/brain-game$ which pip
/home/elias/anaconda3/envs/brain-game2/bin/pip 
```
 - Installera brainflow: `python -m pip install brainflow`
 - Nu kan du också installera fler användbara bibilotek i din conda-miljö, såsom NumPy, SciPy, SciKit-Learn, Matplotlib osv. Exempel på installation: `conda install numpy scipy matplotlib scikit-learn`.
 
 - Verifiera att brainflow finns tillgänglig i python. Starta python genom att köra `python` och där efter testa importera brainflow med `import brainflow as bf`. Om du inte får något felmeddelande så bör allting fungera som det ska.
 
