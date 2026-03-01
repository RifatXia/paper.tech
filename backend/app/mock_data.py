"""Realistic mock data for development — 200 scholars across CS research fields."""

import random

from app.models.schemas import (
    ScholarCard,
    ScoreBreakdown,
    GraphNode,
    GraphEdge,
    ProjectIdea,
)

# ---------------------------------------------------------------------------
# 200 scholars across ML, NLP, CV, Robotics, RL, Systems, and more
# ---------------------------------------------------------------------------

_RAW_SCHOLARS = [
    # --- Machine Learning (General) ---
    {"id": "s1", "name": "Dr. Amara Osei", "aff": "MIT CSAIL", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 42, "papers": 87, "topics": ["KV cache compression", "transformer inference", "systems for ML"]},
    {"id": "s2", "name": "Prof. Liang Chen", "aff": "Stanford NLP Group", "uni": "Stanford University", "city": "Stanford", "state": "California", "country": "US", "h": 58, "papers": 134, "topics": ["efficient transformers", "long-context models", "attention mechanisms"]},
    {"id": "s3", "name": "Dr. Sofia Rodriguez", "aff": "CMU LTI", "uni": "Carnegie Mellon University", "city": "Pittsburgh", "state": "Pennsylvania", "country": "US", "h": 35, "papers": 62, "topics": ["model compression", "quantization", "edge deployment"]},
    {"id": "s4", "name": "Prof. Raj Patel", "aff": "UC Berkeley BAIR", "uni": "University of California, Berkeley", "city": "Berkeley", "state": "California", "country": "US", "h": 47, "papers": 95, "topics": ["speculative decoding", "LLM serving", "batched inference"]},
    {"id": "s5", "name": "Dr. Yuki Tanaka", "aff": "University of Tokyo IST", "uni": "University of Tokyo", "city": "Tokyo", "state": "Tokyo", "country": "JP", "h": 29, "papers": 48, "topics": ["mixture of experts", "sparse models", "distributed inference"]},
    {"id": "s6", "name": "Prof. Elena Vasquez", "aff": "ETH Zurich ML Lab", "uni": "ETH Zurich", "city": "Zurich", "state": "Zurich", "country": "CH", "h": 52, "papers": 110, "topics": ["Bayesian deep learning", "uncertainty estimation", "probabilistic models"]},
    {"id": "s7", "name": "Dr. James Mwangi", "aff": "Oxford ML Group", "uni": "University of Oxford", "city": "Oxford", "state": "Oxfordshire", "country": "GB", "h": 38, "papers": 72, "topics": ["neural architecture search", "AutoML", "hyperparameter optimization"]},
    {"id": "s8", "name": "Prof. Mei-Ling Wu", "aff": "Tsinghua AIR", "uni": "Tsinghua University", "city": "Beijing", "state": "Beijing", "country": "CN", "h": 61, "papers": 145, "topics": ["federated learning", "privacy-preserving ML", "distributed optimization"]},
    {"id": "s9", "name": "Dr. Andreas Hoffmann", "aff": "Max Planck IS", "uni": "Max Planck Institute", "city": "Tubingen", "state": "Baden-Wurttemberg", "country": "DE", "h": 44, "papers": 89, "topics": ["causal inference", "causal discovery", "invariant risk minimization"]},
    {"id": "s10", "name": "Prof. Sarah Mitchell", "aff": "Princeton ML Theory", "uni": "Princeton University", "city": "Princeton", "state": "New Jersey", "country": "US", "h": 39, "papers": 67, "topics": ["optimization theory", "convergence analysis", "stochastic gradient methods"]},

    # --- Natural Language Processing ---
    {"id": "s11", "name": "Prof. David Kim", "aff": "UW NLP", "uni": "University of Washington", "city": "Seattle", "state": "Washington", "country": "US", "h": 55, "papers": 128, "topics": ["question answering", "reading comprehension", "knowledge-grounded QA"]},
    {"id": "s12", "name": "Dr. Fatima Al-Hassan", "aff": "NYU CILVR", "uni": "New York University", "city": "New York", "state": "New York", "country": "US", "h": 41, "papers": 83, "topics": ["multilingual NLP", "cross-lingual transfer", "low-resource languages"]},
    {"id": "s13", "name": "Prof. Marco Rossi", "aff": "FAIR Paris", "uni": "Meta AI Research", "city": "Paris", "state": "Ile-de-France", "country": "FR", "h": 63, "papers": 152, "topics": ["large language models", "instruction tuning", "RLHF"]},
    {"id": "s14", "name": "Dr. Priya Sharma", "aff": "IIT Delhi NLP", "uni": "Indian Institute of Technology Delhi", "city": "New Delhi", "state": "Delhi", "country": "IN", "h": 33, "papers": 58, "topics": ["sentiment analysis", "opinion mining", "aspect-based sentiment"]},
    {"id": "s15", "name": "Prof. Thomas Anderson", "aff": "Edinburgh NLP", "uni": "University of Edinburgh", "city": "Edinburgh", "state": "Scotland", "country": "GB", "h": 48, "papers": 97, "topics": ["machine translation", "neural MT", "multimodal translation"]},
    {"id": "s16", "name": "Dr. Aisha Okonkwo", "aff": "Google DeepMind", "uni": "Google DeepMind", "city": "London", "state": "England", "country": "GB", "h": 51, "papers": 104, "topics": ["dialogue systems", "conversational AI", "open-domain chat"]},
    {"id": "s17", "name": "Prof. Hiroshi Nakamura", "aff": "NAIST NLP", "uni": "Nara Institute of Science and Technology", "city": "Nara", "state": "Nara", "country": "JP", "h": 36, "papers": 69, "topics": ["text summarization", "abstractive summarization", "document understanding"]},
    {"id": "s18", "name": "Dr. Laura Fischer", "aff": "TU Munich NLP", "uni": "Technical University of Munich", "city": "Munich", "state": "Bavaria", "country": "DE", "h": 30, "papers": 52, "topics": ["information extraction", "relation extraction", "event detection"]},
    {"id": "s19", "name": "Prof. Carlos Mendez", "aff": "UNAM Computation", "uni": "National Autonomous University of Mexico", "city": "Mexico City", "state": "CDMX", "country": "MX", "h": 27, "papers": 44, "topics": ["named entity recognition", "sequence labeling", "biomedical NLP"]},
    {"id": "s20", "name": "Dr. Zhen Li", "aff": "Peking University NLP", "uni": "Peking University", "city": "Beijing", "state": "Beijing", "country": "CN", "h": 45, "papers": 91, "topics": ["text generation", "controlled generation", "constrained decoding"]},

    # --- Computer Vision ---
    {"id": "s21", "name": "Prof. Anna Petrov", "aff": "EPFL CVLab", "uni": "EPFL", "city": "Lausanne", "state": "Vaud", "country": "CH", "h": 56, "papers": 119, "topics": ["object detection", "3D object detection", "point cloud processing"]},
    {"id": "s22", "name": "Dr. Michael Chang", "aff": "Georgia Tech CV", "uni": "Georgia Institute of Technology", "city": "Atlanta", "state": "Georgia", "country": "US", "h": 43, "papers": 88, "topics": ["image segmentation", "panoptic segmentation", "scene understanding"]},
    {"id": "s23", "name": "Prof. Nadia Kowalski", "aff": "INRIA Grenoble", "uni": "INRIA", "city": "Grenoble", "state": "Auvergne-Rhone-Alpes", "country": "FR", "h": 49, "papers": 101, "topics": ["visual SLAM", "depth estimation", "3D reconstruction"]},
    {"id": "s24", "name": "Dr. Ravi Krishnan", "aff": "IISc Bangalore CV", "uni": "Indian Institute of Science", "city": "Bangalore", "state": "Karnataka", "country": "IN", "h": 37, "papers": 74, "topics": ["face recognition", "face synthesis", "deepfake detection"]},
    {"id": "s25", "name": "Prof. Jessica Park", "aff": "KAIST Vision", "uni": "KAIST", "city": "Daejeon", "state": "Daejeon", "country": "KR", "h": 46, "papers": 93, "topics": ["video understanding", "action recognition", "temporal modeling"]},
    {"id": "s26", "name": "Dr. Oliver Brown", "aff": "Cornell Tech CV", "uni": "Cornell University", "city": "New York", "state": "New York", "country": "US", "h": 34, "papers": 63, "topics": ["image generation", "diffusion models", "text-to-image synthesis"]},
    {"id": "s27", "name": "Prof. Wei Zhang", "aff": "HKUST Vision", "uni": "Hong Kong University of Science and Technology", "city": "Hong Kong", "state": "Hong Kong", "country": "HK", "h": 53, "papers": 112, "topics": ["visual transformers", "vision-language models", "image-text retrieval"]},
    {"id": "s28", "name": "Dr. Maria Santos", "aff": "IST Lisbon CV", "uni": "Instituto Superior Tecnico", "city": "Lisbon", "state": "Lisbon", "country": "PT", "h": 31, "papers": 55, "topics": ["medical image analysis", "pathology detection", "radiology AI"]},
    {"id": "s29", "name": "Prof. Daniel Lee", "aff": "Samsung AI Center", "uni": "Seoul National University", "city": "Seoul", "state": "Seoul", "country": "KR", "h": 40, "papers": 82, "topics": ["pose estimation", "human mesh recovery", "motion capture"]},
    {"id": "s30", "name": "Dr. Chloe Dubois", "aff": "CNRS Vision", "uni": "CNRS", "city": "Paris", "state": "Ile-de-France", "country": "FR", "h": 28, "papers": 46, "topics": ["optical flow", "video prediction", "motion estimation"]},

    # --- Reinforcement Learning ---
    {"id": "s31", "name": "Prof. Alex Turner", "aff": "DeepMind RL", "uni": "Google DeepMind", "city": "London", "state": "England", "country": "GB", "h": 59, "papers": 137, "topics": ["multi-agent RL", "cooperative learning", "emergent communication"]},
    {"id": "s32", "name": "Dr. Nina Volkov", "aff": "Mila Quebec", "uni": "Universite de Montreal", "city": "Montreal", "state": "Quebec", "country": "CA", "h": 44, "papers": 90, "topics": ["offline RL", "batch reinforcement learning", "conservative Q-learning"]},
    {"id": "s33", "name": "Prof. Kevin O'Brien", "aff": "UC San Diego RL", "uni": "University of California, San Diego", "city": "San Diego", "state": "California", "country": "US", "h": 36, "papers": 68, "topics": ["model-based RL", "world models", "planning with learned dynamics"]},
    {"id": "s34", "name": "Dr. Sana Malik", "aff": "Allen AI", "uni": "Allen Institute for AI", "city": "Seattle", "state": "Washington", "country": "US", "h": 32, "papers": 57, "topics": ["reward modeling", "RLHF", "preference learning"]},
    {"id": "s35", "name": "Prof. Takeshi Yamamoto", "aff": "RIKEN AIP", "uni": "RIKEN", "city": "Tokyo", "state": "Tokyo", "country": "JP", "h": 41, "papers": 84, "topics": ["safe RL", "constrained optimization", "risk-sensitive learning"]},
    {"id": "s36", "name": "Dr. Emma Wilson", "aff": "Cambridge ML", "uni": "University of Cambridge", "city": "Cambridge", "state": "Cambridgeshire", "country": "GB", "h": 38, "papers": 73, "topics": ["meta-reinforcement learning", "few-shot RL", "task transfer"]},
    {"id": "s37", "name": "Prof. Arjun Reddy", "aff": "IIT Bombay RL", "uni": "Indian Institute of Technology Bombay", "city": "Mumbai", "state": "Maharashtra", "country": "IN", "h": 29, "papers": 49, "topics": ["hierarchical RL", "options framework", "skill discovery"]},
    {"id": "s38", "name": "Dr. Lisa Bergmann", "aff": "Bosch AI", "uni": "University of Stuttgart", "city": "Stuttgart", "state": "Baden-Wurttemberg", "country": "DE", "h": 26, "papers": 42, "topics": ["sim-to-real transfer", "domain randomization", "robust policies"]},

    # --- Robotics ---
    {"id": "s39", "name": "Prof. Roberto Colombo", "aff": "IIT Genova", "uni": "Italian Institute of Technology", "city": "Genova", "state": "Liguria", "country": "IT", "h": 50, "papers": 106, "topics": ["humanoid robotics", "bipedal locomotion", "whole-body control"]},
    {"id": "s40", "name": "Dr. Hannah Kim", "aff": "MIT CSAIL Robotics", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 39, "papers": 76, "topics": ["manipulation planning", "grasp synthesis", "dexterous manipulation"]},
    {"id": "s41", "name": "Prof. Jun Liu", "aff": "NUS Robotics", "uni": "National University of Singapore", "city": "Singapore", "state": "Singapore", "country": "SG", "h": 45, "papers": 92, "topics": ["autonomous driving", "motion planning", "trajectory optimization"]},
    {"id": "s42", "name": "Dr. Catherine Wright", "aff": "CMU RI", "uni": "Carnegie Mellon University", "city": "Pittsburgh", "state": "Pennsylvania", "country": "US", "h": 37, "papers": 71, "topics": ["swarm robotics", "multi-robot coordination", "formation control"]},
    {"id": "s43", "name": "Prof. Kenji Suzuki", "aff": "Osaka University", "uni": "Osaka University", "city": "Osaka", "state": "Osaka", "country": "JP", "h": 33, "papers": 60, "topics": ["soft robotics", "compliant actuators", "bio-inspired design"]},
    {"id": "s44", "name": "Dr. Ahmed Hassan", "aff": "KAUST Robotics", "uni": "King Abdullah University of Science and Technology", "city": "Thuwal", "state": "Makkah", "country": "SA", "h": 28, "papers": 47, "topics": ["aerial robotics", "drone navigation", "UAV planning"]},
    {"id": "s45", "name": "Prof. Michelle Torres", "aff": "ETH ASL", "uni": "ETH Zurich", "city": "Zurich", "state": "Zurich", "country": "CH", "h": 42, "papers": 86, "topics": ["robot learning from demonstration", "imitation learning", "learning from human feedback"]},

    # --- Graph Neural Networks ---
    {"id": "s46", "name": "Prof. Jure Petrovic", "aff": "Stanford SNAP", "uni": "Stanford University", "city": "Stanford", "state": "California", "country": "US", "h": 64, "papers": 158, "topics": ["graph neural networks", "knowledge graphs", "graph representation learning"]},
    {"id": "s47", "name": "Dr. Yifan Wang", "aff": "UCLA Graph Lab", "uni": "University of California, Los Angeles", "city": "Los Angeles", "state": "California", "country": "US", "h": 40, "papers": 80, "topics": ["heterogeneous graphs", "graph transformers", "spectral methods"]},
    {"id": "s48", "name": "Prof. Eva Lindqvist", "aff": "KTH ML", "uni": "KTH Royal Institute of Technology", "city": "Stockholm", "state": "Stockholm", "country": "SE", "h": 35, "papers": 66, "topics": ["temporal graphs", "dynamic networks", "link prediction"]},
    {"id": "s49", "name": "Dr. Benjamin Nwosu", "aff": "UCL Graph", "uni": "University College London", "city": "London", "state": "England", "country": "GB", "h": 31, "papers": 54, "topics": ["molecular graphs", "drug discovery", "property prediction"]},
    {"id": "s50", "name": "Prof. Xiaoyu Huang", "aff": "Zhejiang University", "uni": "Zhejiang University", "city": "Hangzhou", "state": "Zhejiang", "country": "CN", "h": 43, "papers": 87, "topics": ["graph generation", "molecular generation", "graph VAE"]},

    # --- Generative AI ---
    {"id": "s51", "name": "Prof. Rachel Green", "aff": "OpenAI", "uni": "OpenAI", "city": "San Francisco", "state": "California", "country": "US", "h": 57, "papers": 122, "topics": ["diffusion models", "score-based generative models", "image synthesis"]},
    {"id": "s52", "name": "Dr. Karthik Subramaniam", "aff": "Google Brain", "uni": "Google Research", "city": "Mountain View", "state": "California", "country": "US", "h": 48, "papers": 99, "topics": ["flow matching", "continuous normalizing flows", "density estimation"]},
    {"id": "s53", "name": "Prof. Isabelle Martin", "aff": "Mila", "uni": "Universite de Montreal", "city": "Montreal", "state": "Quebec", "country": "CA", "h": 54, "papers": 116, "topics": ["variational autoencoders", "latent space models", "disentangled representations"]},
    {"id": "s54", "name": "Dr. Noah Williams", "aff": "Adobe Research", "uni": "Adobe Research", "city": "San Jose", "state": "California", "country": "US", "h": 36, "papers": 65, "topics": ["video generation", "temporal diffusion", "text-to-video"]},
    {"id": "s55", "name": "Prof. Soo-Young Lee", "aff": "POSTECH AI", "uni": "POSTECH", "city": "Pohang", "state": "Gyeongsang", "country": "KR", "h": 42, "papers": 85, "topics": ["3D generation", "neural radiance fields", "3D-aware synthesis"]},
    {"id": "s56", "name": "Dr. Patrick O'Connor", "aff": "Stability AI", "uni": "Stability AI", "city": "London", "state": "England", "country": "GB", "h": 33, "papers": 59, "topics": ["text-to-image", "prompt engineering", "controllable generation"]},
    {"id": "s57", "name": "Prof. Ayumi Sato", "aff": "University of Tokyo Gen", "uni": "University of Tokyo", "city": "Tokyo", "state": "Tokyo", "country": "JP", "h": 38, "papers": 74, "topics": ["music generation", "audio synthesis", "multimodal generation"]},

    # --- Speech & Audio ---
    {"id": "s58", "name": "Prof. George Papadopoulos", "aff": "JHU CLSP", "uni": "Johns Hopkins University", "city": "Baltimore", "state": "Maryland", "country": "US", "h": 50, "papers": 108, "topics": ["automatic speech recognition", "end-to-end ASR", "self-supervised speech"]},
    {"id": "s59", "name": "Dr. Ananya Das", "aff": "Microsoft Speech", "uni": "Microsoft Research", "city": "Redmond", "state": "Washington", "country": "US", "h": 39, "papers": 77, "topics": ["text-to-speech", "neural vocoder", "expressive synthesis"]},
    {"id": "s60", "name": "Prof. Henrik Larsen", "aff": "Aalborg Audio", "uni": "Aalborg University", "city": "Aalborg", "state": "Nordjylland", "country": "DK", "h": 34, "papers": 64, "topics": ["speaker diarization", "voice cloning", "speaker verification"]},
    {"id": "s61", "name": "Dr. Mia Thompson", "aff": "Apple ML", "uni": "Apple", "city": "Cupertino", "state": "California", "country": "US", "h": 30, "papers": 51, "topics": ["keyword spotting", "on-device speech", "wake word detection"]},

    # --- Information Retrieval ---
    {"id": "s62", "name": "Prof. Chris Davis", "aff": "UMass CIIR", "uni": "University of Massachusetts Amherst", "city": "Amherst", "state": "Massachusetts", "country": "US", "h": 52, "papers": 114, "topics": ["dense retrieval", "passage ranking", "neural information retrieval"]},
    {"id": "s63", "name": "Dr. Ling Xu", "aff": "Baidu NLP", "uni": "Baidu Research", "city": "Beijing", "state": "Beijing", "country": "CN", "h": 44, "papers": 90, "topics": ["semantic search", "query understanding", "search ranking"]},
    {"id": "s64", "name": "Prof. Andrew Roberts", "aff": "Waterloo IR", "uni": "University of Waterloo", "city": "Waterloo", "state": "Ontario", "country": "CA", "h": 46, "papers": 94, "topics": ["conversational search", "retrieval-augmented generation", "RAG systems"]},
    {"id": "s65", "name": "Dr. Julia Novak", "aff": "TU Wien IR", "uni": "TU Wien", "city": "Vienna", "state": "Vienna", "country": "AT", "h": 29, "papers": 48, "topics": ["recommendation systems", "collaborative filtering", "session-based recommendations"]},

    # --- AI for Science ---
    {"id": "s66", "name": "Prof. Martin Fischer", "aff": "Caltech AI4Science", "uni": "California Institute of Technology", "city": "Pasadena", "state": "California", "country": "US", "h": 55, "papers": 121, "topics": ["protein structure prediction", "molecular dynamics", "scientific ML"]},
    {"id": "s67", "name": "Dr. Olga Petrova", "aff": "Skoltech AI", "uni": "Skolkovo Institute of Science and Technology", "city": "Moscow", "state": "Moscow", "country": "RU", "h": 37, "papers": 70, "topics": ["materials discovery", "crystal structure prediction", "inverse design"]},
    {"id": "s68", "name": "Prof. Robert Harris", "aff": "MIT CSAIL Bio", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 48, "papers": 100, "topics": ["drug discovery", "molecular property prediction", "virtual screening"]},
    {"id": "s69", "name": "Dr. Sunita Rao", "aff": "IISc Comp Bio", "uni": "Indian Institute of Science", "city": "Bangalore", "state": "Karnataka", "country": "IN", "h": 32, "papers": 56, "topics": ["genomics ML", "gene expression analysis", "single-cell analysis"]},
    {"id": "s70", "name": "Prof. William Clark", "aff": "Stanford Bio-X", "uni": "Stanford University", "city": "Stanford", "state": "California", "country": "US", "h": 60, "papers": 142, "topics": ["clinical NLP", "electronic health records", "medical AI"]},

    # --- Trustworthy AI / Safety ---
    {"id": "s71", "name": "Prof. Grace Hopper", "aff": "UC Berkeley Safety", "uni": "University of California, Berkeley", "city": "Berkeley", "state": "California", "country": "US", "h": 46, "papers": 94, "topics": ["AI safety", "alignment", "red teaming"]},
    {"id": "s72", "name": "Dr. Mohammed Ali", "aff": "Anthropic", "uni": "Anthropic", "city": "San Francisco", "state": "California", "country": "US", "h": 40, "papers": 81, "topics": ["constitutional AI", "scalable oversight", "interpretability"]},
    {"id": "s73", "name": "Prof. Diana Popescu", "aff": "Oxford Ethics", "uni": "University of Oxford", "city": "Oxford", "state": "Oxfordshire", "country": "GB", "h": 35, "papers": 64, "topics": ["fairness in ML", "algorithmic bias", "equitable AI"]},
    {"id": "s74", "name": "Dr. Samuel Okafor", "aff": "CHAI Berkeley", "uni": "University of California, Berkeley", "city": "Berkeley", "state": "California", "country": "US", "h": 33, "papers": 58, "topics": ["robustness", "adversarial examples", "certified defenses"]},
    {"id": "s75", "name": "Prof. Ingrid Muller", "aff": "MPI Ethics", "uni": "Max Planck Institute", "city": "Berlin", "state": "Berlin", "country": "DE", "h": 28, "papers": 45, "topics": ["explainable AI", "feature attribution", "model transparency"]},

    # --- Computer Vision (additional) ---
    {"id": "s76", "name": "Dr. Lucas Martin", "aff": "NVIDIA Research", "uni": "NVIDIA", "city": "Santa Clara", "state": "California", "country": "US", "h": 47, "papers": 96, "topics": ["neural rendering", "gaussian splatting", "real-time rendering"]},
    {"id": "s77", "name": "Prof. Hana Yoshida", "aff": "NAIST Vision", "uni": "Nara Institute of Science and Technology", "city": "Nara", "state": "Nara", "country": "JP", "h": 35, "papers": 67, "topics": ["document analysis", "OCR", "scene text recognition"]},
    {"id": "s78", "name": "Dr. Victor Ivanov", "aff": "Samsung AI Moscow", "uni": "Samsung AI Center", "city": "Moscow", "state": "Moscow", "country": "RU", "h": 30, "papers": 52, "topics": ["image super-resolution", "image restoration", "denoising"]},
    {"id": "s79", "name": "Prof. Natalie Cooper", "aff": "Michigan Vision", "uni": "University of Michigan", "city": "Ann Arbor", "state": "Michigan", "country": "US", "h": 41, "papers": 83, "topics": ["visual question answering", "visual reasoning", "vision-language understanding"]},
    {"id": "s80", "name": "Dr. Paulo Ferreira", "aff": "UNICAMP CV", "uni": "University of Campinas", "city": "Campinas", "state": "Sao Paulo", "country": "BR", "h": 25, "papers": 41, "topics": ["remote sensing", "satellite imagery", "geospatial AI"]},

    # --- NLP (additional) ---
    {"id": "s81", "name": "Prof. Elizabeth Taylor", "aff": "Allen NLP", "uni": "Allen Institute for AI", "city": "Seattle", "state": "Washington", "country": "US", "h": 53, "papers": 115, "topics": ["commonsense reasoning", "knowledge bases", "structured prediction"]},
    {"id": "s82", "name": "Dr. Amit Gupta", "aff": "IIT Kanpur NLP", "uni": "Indian Institute of Technology Kanpur", "city": "Kanpur", "state": "Uttar Pradesh", "country": "IN", "h": 31, "papers": 53, "topics": ["code generation", "program synthesis", "code understanding"]},
    {"id": "s83", "name": "Prof. Sophie Blanc", "aff": "Sorbonne NLP", "uni": "Sorbonne Universite", "city": "Paris", "state": "Ile-de-France", "country": "FR", "h": 37, "papers": 71, "topics": ["discourse analysis", "coreference resolution", "pragmatics"]},
    {"id": "s84", "name": "Dr. Ryan Foster", "aff": "Cohere Research", "uni": "Cohere", "city": "Toronto", "state": "Ontario", "country": "CA", "h": 34, "papers": 61, "topics": ["embedding models", "sentence embeddings", "contrastive learning for NLP"]},
    {"id": "s85", "name": "Prof. Jing Zhao", "aff": "Fudan NLP", "uni": "Fudan University", "city": "Shanghai", "state": "Shanghai", "country": "CN", "h": 42, "papers": 86, "topics": ["text classification", "few-shot text learning", "prompt-based learning"]},

    # --- ML Theory ---
    {"id": "s86", "name": "Prof. Peter Bartlett", "aff": "Berkeley Theory", "uni": "University of California, Berkeley", "city": "Berkeley", "state": "California", "country": "US", "h": 62, "papers": 148, "topics": ["learning theory", "generalization bounds", "PAC learning"]},
    {"id": "s87", "name": "Dr. Claire Dupont", "aff": "INRIA Theory", "uni": "INRIA", "city": "Paris", "state": "Ile-de-France", "country": "FR", "h": 35, "papers": 63, "topics": ["online learning", "bandit algorithms", "regret minimization"]},
    {"id": "s88", "name": "Prof. Nathan Shapiro", "aff": "MIT EECS Theory", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 44, "papers": 88, "topics": ["kernel methods", "reproducing kernel Hilbert spaces", "random features"]},
    {"id": "s89", "name": "Dr. Rina Tanaka", "aff": "ISM Tokyo", "uni": "Institute of Statistical Mathematics", "city": "Tokyo", "state": "Tokyo", "country": "JP", "h": 30, "papers": 50, "topics": ["statistical learning theory", "high-dimensional statistics", "minimax rates"]},

    # --- Systems for ML ---
    {"id": "s90", "name": "Prof. Steven Liu", "aff": "CMU Systems", "uni": "Carnegie Mellon University", "city": "Pittsburgh", "state": "Pennsylvania", "country": "US", "h": 49, "papers": 102, "topics": ["ML compilers", "operator fusion", "graph optimization"]},
    {"id": "s91", "name": "Dr. Karen White", "aff": "Google Systems", "uni": "Google Research", "city": "Mountain View", "state": "California", "country": "US", "h": 43, "papers": 87, "topics": ["distributed training", "data parallelism", "pipeline parallelism"]},
    {"id": "s92", "name": "Prof. Deepak Agrawal", "aff": "Microsoft Research", "uni": "Microsoft Research", "city": "Redmond", "state": "Washington", "country": "US", "h": 51, "papers": 109, "topics": ["memory-efficient training", "gradient checkpointing", "mixed-precision training"]},
    {"id": "s93", "name": "Dr. Marcus Johnson", "aff": "Meta FAIR Systems", "uni": "Meta AI Research", "city": "Menlo Park", "state": "California", "country": "US", "h": 38, "papers": 72, "topics": ["model parallelism", "tensor parallelism", "FSDP"]},

    # --- Multimodal ---
    {"id": "s94", "name": "Prof. Emily Watson", "aff": "Salesforce AI", "uni": "Salesforce Research", "city": "Palo Alto", "state": "California", "country": "US", "h": 55, "papers": 120, "topics": ["vision-language pretraining", "multimodal fusion", "BLIP models"]},
    {"id": "s95", "name": "Dr. Tao Chen", "aff": "NTU Multimodal", "uni": "Nanyang Technological University", "city": "Singapore", "state": "Singapore", "country": "SG", "h": 41, "papers": 84, "topics": ["video-language models", "multimodal reasoning", "visual grounding"]},
    {"id": "s96", "name": "Prof. Ashley Martin", "aff": "UT Austin Multimodal", "uni": "University of Texas at Austin", "city": "Austin", "state": "Texas", "country": "US", "h": 44, "papers": 89, "topics": ["embodied AI", "vision-language navigation", "instruction following"]},
    {"id": "s97", "name": "Dr. Giulia Romano", "aff": "UniPD Multimodal", "uni": "University of Padova", "city": "Padova", "state": "Veneto", "country": "IT", "h": 29, "papers": 48, "topics": ["cross-modal retrieval", "image captioning", "visual storytelling"]},

    # --- Self-Supervised Learning ---
    {"id": "s98", "name": "Prof. Yann Bengio", "aff": "Meta FAIR SSL", "uni": "Meta AI Research", "city": "New York", "state": "New York", "country": "US", "h": 58, "papers": 130, "topics": ["self-supervised learning", "contrastive learning", "masked image modeling"]},
    {"id": "s99", "name": "Dr. Sandra Eriksson", "aff": "Lund University ML", "uni": "Lund University", "city": "Lund", "state": "Skane", "country": "SE", "h": 32, "papers": 55, "topics": ["joint embedding methods", "JEPA", "non-contrastive learning"]},
    {"id": "s100", "name": "Prof. Mark Thompson", "aff": "Toronto DL", "uni": "University of Toronto", "city": "Toronto", "state": "Ontario", "country": "CA", "h": 47, "papers": 97, "topics": ["representation learning", "transfer learning", "foundation models"]},

    # --- Time Series ---
    {"id": "s101", "name": "Prof. Zhiyuan Ma", "aff": "SJTU Data", "uni": "Shanghai Jiao Tong University", "city": "Shanghai", "state": "Shanghai", "country": "CN", "h": 39, "papers": 76, "topics": ["time series forecasting", "temporal pattern mining", "anomaly detection"]},
    {"id": "s102", "name": "Dr. Olivia Scott", "aff": "Amazon Science", "uni": "Amazon Research", "city": "Seattle", "state": "Washington", "country": "US", "h": 35, "papers": 64, "topics": ["demand forecasting", "probabilistic forecasting", "time series foundation models"]},
    {"id": "s103", "name": "Prof. Christoph Wagner", "aff": "TU Berlin", "uni": "Technical University of Berlin", "city": "Berlin", "state": "Berlin", "country": "DE", "h": 33, "papers": 59, "topics": ["signal processing", "spectral analysis", "wavelet methods"]},

    # --- Tabular / AutoML ---
    {"id": "s104", "name": "Prof. Frank Hutter", "aff": "Freiburg AutoML", "uni": "University of Freiburg", "city": "Freiburg", "state": "Baden-Wurttemberg", "country": "DE", "h": 56, "papers": 124, "topics": ["AutoML", "neural architecture search", "hyperparameter optimization"]},
    {"id": "s105", "name": "Dr. Rebecca Stone", "aff": "AWS AI Labs", "uni": "Amazon Research", "city": "Seattle", "state": "Washington", "country": "US", "h": 38, "papers": 73, "topics": ["tabular learning", "tree-based models", "gradient boosting"]},
    {"id": "s106", "name": "Prof. Yuichi Honda", "aff": "RIKEN AutoML", "uni": "RIKEN", "city": "Kobe", "state": "Hyogo", "country": "JP", "h": 31, "papers": 53, "topics": ["data augmentation", "synthetic data", "data-centric AI"]},

    # --- Optimization ---
    {"id": "s107", "name": "Prof. Suvrit Sra", "aff": "MIT Optimization", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 45, "papers": 92, "topics": ["non-convex optimization", "Riemannian optimization", "geodesic convexity"]},
    {"id": "s108", "name": "Dr. Konstantin Petrov", "aff": "EPFL Optimization", "uni": "EPFL", "city": "Lausanne", "state": "Vaud", "country": "CH", "h": 37, "papers": 69, "topics": ["first-order methods", "momentum methods", "adaptive learning rates"]},
    {"id": "s109", "name": "Prof. Jennifer Adams", "aff": "Georgia Tech Opt", "uni": "Georgia Institute of Technology", "city": "Atlanta", "state": "Georgia", "country": "US", "h": 41, "papers": 82, "topics": ["combinatorial optimization", "integer programming", "neural combinatorial solvers"]},

    # --- Privacy & Security ---
    {"id": "s110", "name": "Prof. David Zhao", "aff": "Stanford Security", "uni": "Stanford University", "city": "Stanford", "state": "California", "country": "US", "h": 48, "papers": 98, "topics": ["differential privacy", "private machine learning", "federated analytics"]},
    {"id": "s111", "name": "Dr. Leila Ahmadi", "aff": "CISPA Helmholtz", "uni": "CISPA Helmholtz Center", "city": "Saarbrucken", "state": "Saarland", "country": "DE", "h": 34, "papers": 62, "topics": ["adversarial ML", "model stealing", "membership inference"]},
    {"id": "s112", "name": "Prof. Brian Chen", "aff": "CMU Security", "uni": "Carnegie Mellon University", "city": "Pittsburgh", "state": "Pennsylvania", "country": "US", "h": 43, "papers": 88, "topics": ["ML security", "backdoor attacks", "model watermarking"]},

    # --- HCI & Visualization ---
    {"id": "s113", "name": "Prof. Alice Yang", "aff": "MIT Media Lab", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 40, "papers": 79, "topics": ["human-AI interaction", "interactive ML", "mixed-initiative systems"]},
    {"id": "s114", "name": "Dr. Tom Nielsen", "aff": "Aarhus HCI", "uni": "Aarhus University", "city": "Aarhus", "state": "Midtjylland", "country": "DK", "h": 33, "papers": 57, "topics": ["data visualization", "visual analytics", "exploratory analysis tools"]},
    {"id": "s115", "name": "Prof. Maya Patel", "aff": "Georgia Tech HCI", "uni": "Georgia Institute of Technology", "city": "Atlanta", "state": "Georgia", "country": "US", "h": 38, "papers": 72, "topics": ["AI-assisted creativity", "generative design tools", "human-in-the-loop"]},

    # --- Knowledge Representation ---
    {"id": "s116", "name": "Prof. Richard Thompson", "aff": "Stanford KR", "uni": "Stanford University", "city": "Stanford", "state": "California", "country": "US", "h": 50, "papers": 107, "topics": ["knowledge graph completion", "link prediction", "entity alignment"]},
    {"id": "s117", "name": "Dr. Fei Chen", "aff": "Alibaba DAMO", "uni": "Alibaba DAMO Academy", "city": "Hangzhou", "state": "Zhejiang", "country": "CN", "h": 42, "papers": 85, "topics": ["knowledge distillation", "teacher-student networks", "model compression"]},
    {"id": "s118", "name": "Prof. Stephanie Moore", "aff": "Illinois UIUC", "uni": "University of Illinois Urbana-Champaign", "city": "Champaign", "state": "Illinois", "country": "US", "h": 39, "papers": 75, "topics": ["ontology learning", "taxonomy construction", "concept extraction"]},

    # --- Edge AI / Embedded ---
    {"id": "s119", "name": "Prof. Hyun-Joon Kim", "aff": "Samsung Semiconductor", "uni": "Samsung Research", "city": "Suwon", "state": "Gyeonggi", "country": "KR", "h": 36, "papers": 68, "topics": ["neural network pruning", "efficient inference", "hardware-aware NAS"]},
    {"id": "s120", "name": "Dr. Pablo Garcia", "aff": "Qualcomm AI", "uni": "Qualcomm Research", "city": "San Diego", "state": "California", "country": "US", "h": 32, "papers": 56, "topics": ["on-device ML", "TinyML", "microcontroller inference"]},
    {"id": "s121", "name": "Prof. Angela Russo", "aff": "Politecnico Milano", "uni": "Politecnico di Milano", "city": "Milan", "state": "Lombardy", "country": "IT", "h": 29, "papers": 47, "topics": ["edge computing", "federated edge learning", "split inference"]},

    # --- ML for Climate ---
    {"id": "s122", "name": "Prof. Katherine Harris", "aff": "Stanford Sustainability", "uni": "Stanford University", "city": "Stanford", "state": "California", "country": "US", "h": 44, "papers": 90, "topics": ["climate modeling", "weather prediction", "earth system ML"]},
    {"id": "s123", "name": "Dr. Bjorn Svensson", "aff": "ETH Climate", "uni": "ETH Zurich", "city": "Zurich", "state": "Zurich", "country": "CH", "h": 36, "papers": 67, "topics": ["carbon footprint tracking", "sustainable AI", "green computing"]},
    {"id": "s124", "name": "Prof. Lucia Hernandez", "aff": "UNAM Climate", "uni": "National Autonomous University of Mexico", "city": "Mexico City", "state": "CDMX", "country": "MX", "h": 28, "papers": 45, "topics": ["remote sensing ML", "deforestation detection", "biodiversity monitoring"]},

    # --- Continual / Lifelong Learning ---
    {"id": "s125", "name": "Prof. Tinne Tuytelaars", "aff": "KU Leuven", "uni": "KU Leuven", "city": "Leuven", "state": "Flemish Brabant", "country": "BE", "h": 47, "papers": 95, "topics": ["continual learning", "catastrophic forgetting", "rehearsal methods"]},
    {"id": "s126", "name": "Dr. Jason Park", "aff": "Seoul National U CL", "uni": "Seoul National University", "city": "Seoul", "state": "Seoul", "country": "KR", "h": 33, "papers": 58, "topics": ["class-incremental learning", "exemplar selection", "knowledge consolidation"]},
    {"id": "s127", "name": "Prof. Andrea Rossi", "aff": "University of Pisa", "uni": "University of Pisa", "city": "Pisa", "state": "Tuscany", "country": "IT", "h": 30, "papers": 51, "topics": ["online continual learning", "streaming data", "concept drift"]},

    # --- Multi-Task / Meta-Learning ---
    {"id": "s128", "name": "Prof. Chelsea Finn", "aff": "Stanford IRIS", "uni": "Stanford University", "city": "Stanford", "state": "California", "country": "US", "h": 56, "papers": 118, "topics": ["meta-learning", "few-shot learning", "learning to learn"]},
    {"id": "s129", "name": "Dr. Xiang Li", "aff": "CUHK Meta", "uni": "Chinese University of Hong Kong", "city": "Hong Kong", "state": "Hong Kong", "country": "HK", "h": 37, "papers": 70, "topics": ["multi-task learning", "task relationships", "auxiliary tasks"]},
    {"id": "s130", "name": "Prof. Paul Henderson", "aff": "Edinburgh Meta", "uni": "University of Edinburgh", "city": "Edinburgh", "state": "Scotland", "country": "GB", "h": 32, "papers": 55, "topics": ["task-agnostic representations", "universal models", "model-agnostic methods"]},

    # --- Data-Centric AI ---
    {"id": "s131", "name": "Prof. Andrew Ng", "aff": "Stanford HAI", "uni": "Stanford University", "city": "Stanford", "state": "California", "country": "US", "h": 72, "papers": 180, "topics": ["data-centric AI", "data quality", "label noise"]},
    {"id": "s132", "name": "Dr. Vanessa Chen", "aff": "Snorkel AI", "uni": "Snorkel AI", "city": "Palo Alto", "state": "California", "country": "US", "h": 35, "papers": 62, "topics": ["weak supervision", "programmatic labeling", "data programming"]},
    {"id": "s133", "name": "Prof. Derek Hall", "aff": "Wisconsin Data", "uni": "University of Wisconsin-Madison", "city": "Madison", "state": "Wisconsin", "country": "US", "h": 40, "papers": 78, "topics": ["active learning", "sample selection", "data-efficient learning"]},

    # --- NLP (more) ---
    {"id": "s134", "name": "Prof. Anna Korhonen", "aff": "Cambridge NLP", "uni": "University of Cambridge", "city": "Cambridge", "state": "Cambridgeshire", "country": "GB", "h": 46, "papers": 93, "topics": ["semantic parsing", "meaning representation", "compositional semantics"]},
    {"id": "s135", "name": "Dr. Luis Rivera", "aff": "CMU LTI Spanish", "uni": "Carnegie Mellon University", "city": "Pittsburgh", "state": "Pennsylvania", "country": "US", "h": 30, "papers": 50, "topics": ["hate speech detection", "content moderation", "toxicity classification"]},
    {"id": "s136", "name": "Prof. Minjoon Seo", "aff": "KAIST NLP", "uni": "KAIST", "city": "Daejeon", "state": "Daejeon", "country": "KR", "h": 43, "papers": 87, "topics": ["retrieval-augmented LLMs", "knowledge-intensive NLP", "open-domain QA"]},
    {"id": "s137", "name": "Dr. Hannah Baker", "aff": "Hugging Face", "uni": "Hugging Face", "city": "New York", "state": "New York", "country": "US", "h": 36, "papers": 65, "topics": ["model evaluation", "benchmark design", "LLM leaderboards"]},
    {"id": "s138", "name": "Prof. Danqi Chen", "aff": "Princeton NLP", "uni": "Princeton University", "city": "Princeton", "state": "New Jersey", "country": "US", "h": 51, "papers": 108, "topics": ["open-domain question answering", "dense passage retrieval", "knowledge-intensive tasks"]},

    # --- CV (more) ---
    {"id": "s139", "name": "Prof. Vladlen Koltun", "aff": "Apple Vision Pro", "uni": "Apple", "city": "Cupertino", "state": "California", "country": "US", "h": 60, "papers": 140, "topics": ["dense prediction", "monocular depth", "semantic correspondence"]},
    {"id": "s140", "name": "Dr. Sungjoon Park", "aff": "Naver AI", "uni": "Naver AI Lab", "city": "Seongnam", "state": "Gyeonggi", "country": "KR", "h": 34, "papers": 61, "topics": ["image retrieval", "contrastive visual learning", "visual place recognition"]},
    {"id": "s141", "name": "Prof. Amanda Taylor", "aff": "MIT CSAIL Vision", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 45, "papers": 91, "topics": ["scene generation", "layout-to-image", "compositional generation"]},
    {"id": "s142", "name": "Dr. Florian Mayer", "aff": "TU Munich CV", "uni": "Technical University of Munich", "city": "Munich", "state": "Bavaria", "country": "DE", "h": 38, "papers": 74, "topics": ["3D scene understanding", "indoor mapping", "point cloud segmentation"]},

    # --- Autonomous Vehicles ---
    {"id": "s143", "name": "Prof. Raquel Urtasun", "aff": "Waabi", "uni": "University of Toronto", "city": "Toronto", "state": "Ontario", "country": "CA", "h": 57, "papers": 126, "topics": ["self-driving", "lidar perception", "end-to-end driving"]},
    {"id": "s144", "name": "Dr. Feng Wang", "aff": "Waymo Research", "uni": "Waymo", "city": "Mountain View", "state": "California", "country": "US", "h": 42, "papers": 85, "topics": ["behavior prediction", "trajectory forecasting", "occupancy networks"]},
    {"id": "s145", "name": "Prof. Stefan Roth", "aff": "TU Darmstadt", "uni": "Technical University of Darmstadt", "city": "Darmstadt", "state": "Hesse", "country": "DE", "h": 44, "papers": 89, "topics": ["scene flow", "stereo matching", "automotive perception"]},

    # --- Quantum ML ---
    {"id": "s146", "name": "Prof. Maria Schuld", "aff": "Xanadu", "uni": "Xanadu", "city": "Toronto", "state": "Ontario", "country": "CA", "h": 35, "papers": 63, "topics": ["quantum machine learning", "variational quantum circuits", "quantum kernels"]},
    {"id": "s147", "name": "Dr. Jacob Biamonte", "aff": "Skoltech Quantum", "uni": "Skolkovo Institute of Science and Technology", "city": "Moscow", "state": "Moscow", "country": "RU", "h": 30, "papers": 50, "topics": ["tensor networks", "quantum tensor methods", "quantum complexity"]},

    # --- Audio / Music AI ---
    {"id": "s148", "name": "Prof. Brian McFee", "aff": "NYU Music", "uni": "New York University", "city": "New York", "state": "New York", "country": "US", "h": 38, "papers": 72, "topics": ["music information retrieval", "audio feature extraction", "beat tracking"]},
    {"id": "s149", "name": "Dr. Keunwoo Choi", "aff": "Spotify Research", "uni": "Spotify", "city": "London", "state": "England", "country": "GB", "h": 27, "papers": 44, "topics": ["music recommendation", "audio embeddings", "music tagging"]},

    # --- NLP / Agents ---
    {"id": "s150", "name": "Prof. Shunyu Yao", "aff": "Princeton LM Agents", "uni": "Princeton University", "city": "Princeton", "state": "New Jersey", "country": "US", "h": 34, "papers": 58, "topics": ["LLM agents", "tool use", "reasoning and acting"]},
    {"id": "s151", "name": "Dr. Xinyun Chen", "aff": "Google Brain Agents", "uni": "Google Research", "city": "Mountain View", "state": "California", "country": "US", "h": 36, "papers": 64, "topics": ["code agents", "web agents", "autonomous coding"]},
    {"id": "s152", "name": "Prof. Noah Shinn", "aff": "MIT Agents", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 28, "papers": 43, "topics": ["self-reflection", "iterative refinement", "agent memory"]},

    # --- Geometric DL ---
    {"id": "s153", "name": "Prof. Michael Bronstein", "aff": "Oxford Geometric", "uni": "University of Oxford", "city": "Oxford", "state": "Oxfordshire", "country": "GB", "h": 58, "papers": 132, "topics": ["geometric deep learning", "equivariant networks", "manifold learning"]},
    {"id": "s154", "name": "Dr. Fabian Fuchs", "aff": "Prescient Design", "uni": "Prescient Design", "city": "New York", "state": "New York", "country": "US", "h": 30, "papers": 49, "topics": ["SE(3) equivariance", "spherical CNNs", "rotation-invariant features"]},

    # --- Efficient LLMs ---
    {"id": "s155", "name": "Prof. Song Han", "aff": "MIT EfficientML", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 54, "papers": 117, "topics": ["LLM quantization", "efficient fine-tuning", "hardware-efficient ML"]},
    {"id": "s156", "name": "Dr. Tim Dettmers", "aff": "UW Efficient LLM", "uni": "University of Washington", "city": "Seattle", "state": "Washington", "country": "US", "h": 32, "papers": 54, "topics": ["4-bit quantization", "QLoRA", "memory-efficient fine-tuning"]},
    {"id": "s157", "name": "Prof. Edward Hu", "aff": "Microsoft LoRA", "uni": "Microsoft Research", "city": "Redmond", "state": "Washington", "country": "US", "h": 35, "papers": 60, "topics": ["LoRA", "parameter-efficient fine-tuning", "adapter methods"]},
    {"id": "s158", "name": "Dr. Tri Dao", "aff": "Princeton FlashAttention", "uni": "Princeton University", "city": "Princeton", "state": "New Jersey", "country": "US", "h": 33, "papers": 55, "topics": ["FlashAttention", "IO-aware algorithms", "sub-quadratic attention"]},

    # --- ML for Healthcare ---
    {"id": "s159", "name": "Prof. Marzyeh Ghassemi", "aff": "MIT Health ML", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 43, "papers": 87, "topics": ["clinical prediction", "health equity", "de-identification"]},
    {"id": "s160", "name": "Dr. Shalmali Joshi", "aff": "Columbia Health AI", "uni": "Columbia University", "city": "New York", "state": "New York", "country": "US", "h": 31, "papers": 52, "topics": ["treatment effect estimation", "causal ML for health", "counterfactual reasoning"]},
    {"id": "s161", "name": "Prof. Nigam Shah", "aff": "Stanford Medicine AI", "uni": "Stanford University", "city": "Stanford", "state": "California", "country": "US", "h": 55, "papers": 123, "topics": ["EHR modeling", "clinical trial optimization", "real-world evidence"]},

    # --- Autonomous Systems ---
    {"id": "s162", "name": "Prof. Marco Pavone", "aff": "Stanford ASL", "uni": "Stanford University", "city": "Stanford", "state": "California", "country": "US", "h": 48, "papers": 100, "topics": ["safe autonomy", "stochastic optimal control", "risk-aware planning"]},
    {"id": "s163", "name": "Dr. Angela Schoellig", "aff": "TU Munich Auto", "uni": "Technical University of Munich", "city": "Munich", "state": "Bavaria", "country": "DE", "h": 36, "papers": 66, "topics": ["learning-based control", "safe learning", "Gaussian process control"]},

    # --- Computational Social Science ---
    {"id": "s164", "name": "Prof. David Lazer", "aff": "Northeastern CSS", "uni": "Northeastern University", "city": "Boston", "state": "Massachusetts", "country": "US", "h": 50, "papers": 104, "topics": ["misinformation detection", "social network analysis", "computational social science"]},
    {"id": "s165", "name": "Dr. Emilio Ferrara", "aff": "USC ISI", "uni": "University of Southern California", "city": "Los Angeles", "state": "California", "country": "US", "h": 44, "papers": 89, "topics": ["bot detection", "social media analysis", "information diffusion"]},

    # --- Dense Retrieval / Search ---
    {"id": "s166", "name": "Prof. Jimmy Lin", "aff": "Waterloo NLP", "uni": "University of Waterloo", "city": "Waterloo", "state": "Ontario", "country": "CA", "h": 53, "papers": 116, "topics": ["sparse retrieval", "learned sparse representations", "efficient indexing"]},
    {"id": "s167", "name": "Dr. Nils Reimers", "aff": "Cohere Embeddings", "uni": "Cohere", "city": "Toronto", "state": "Ontario", "country": "CA", "h": 34, "papers": 58, "topics": ["sentence-BERT", "semantic textual similarity", "cross-encoder reranking"]},

    # --- Reinforcement Learning (more) ---
    {"id": "s168", "name": "Prof. Sergey Levine", "aff": "Berkeley RL", "uni": "University of California, Berkeley", "city": "Berkeley", "state": "California", "country": "US", "h": 62, "papers": 150, "topics": ["robot learning", "offline RL for robotics", "decision transformers"]},
    {"id": "s169", "name": "Dr. Aviral Kumar", "aff": "Google Brain RL", "uni": "Google Research", "city": "Mountain View", "state": "California", "country": "US", "h": 35, "papers": 61, "topics": ["conservative Q-learning", "implicit Q-learning", "offline policy selection"]},

    # --- Federated Learning ---
    {"id": "s170", "name": "Prof. Virginia Smith", "aff": "CMU Federated", "uni": "Carnegie Mellon University", "city": "Pittsburgh", "state": "Pennsylvania", "country": "US", "h": 40, "papers": 78, "topics": ["federated optimization", "heterogeneous federations", "personalized FL"]},
    {"id": "s171", "name": "Dr. Peter Kairouz", "aff": "Google FL", "uni": "Google Research", "city": "Mountain View", "state": "California", "country": "US", "h": 38, "papers": 71, "topics": ["secure aggregation", "federated analytics", "private FL"]},

    # --- Document AI ---
    {"id": "s172", "name": "Prof. Lei Li", "aff": "UCSB NLP", "uni": "University of California, Santa Barbara", "city": "Santa Barbara", "state": "California", "country": "US", "h": 42, "papers": 84, "topics": ["document layout analysis", "table extraction", "form understanding"]},
    {"id": "s173", "name": "Dr. Minghao Li", "aff": "Microsoft Document", "uni": "Microsoft Research", "city": "Redmond", "state": "Washington", "country": "US", "h": 30, "papers": 49, "topics": ["document pretraining", "LayoutLM", "multimodal document models"]},

    # --- Bayesian ML ---
    {"id": "s174", "name": "Prof. Zoubin Ghahramani", "aff": "Google Brain Bayesian", "uni": "Google DeepMind", "city": "London", "state": "England", "country": "GB", "h": 68, "papers": 165, "topics": ["Bayesian nonparametrics", "Gaussian processes", "approximate inference"]},
    {"id": "s175", "name": "Dr. Andrew Wilson", "aff": "NYU Bayesian DL", "uni": "New York University", "city": "New York", "state": "New York", "country": "US", "h": 42, "papers": 83, "topics": ["Bayesian deep learning", "loss surfaces", "model selection"]},

    # --- Neuro-symbolic ---
    {"id": "s176", "name": "Prof. Joshua Tenenbaum", "aff": "MIT CoCoSci", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 65, "papers": 156, "topics": ["neuro-symbolic AI", "program induction", "cognitive modeling"]},
    {"id": "s177", "name": "Dr. Catherine Wong", "aff": "MIT Brain+Machines", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 28, "papers": 44, "topics": ["program synthesis from language", "library learning", "abstraction and reasoning"]},

    # --- Social Good ---
    {"id": "s178", "name": "Prof. Milind Tambe", "aff": "Harvard AI for Good", "uni": "Harvard University", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 52, "papers": 112, "topics": ["AI for social good", "public health AI", "game theory for security"]},
    {"id": "s179", "name": "Dr. Rediet Abebe", "aff": "UC Berkeley Social", "uni": "University of California, Berkeley", "city": "Berkeley", "state": "California", "country": "US", "h": 27, "papers": 42, "topics": ["algorithmic fairness", "inequality in algorithms", "mechanism design"]},

    # --- LLM Reasoning ---
    {"id": "s180", "name": "Prof. Jason Wei", "aff": "OpenAI Reasoning", "uni": "OpenAI", "city": "San Francisco", "state": "California", "country": "US", "h": 38, "papers": 70, "topics": ["chain-of-thought reasoning", "emergent abilities", "scaling laws"]},
    {"id": "s181", "name": "Dr. Denny Zhou", "aff": "Google Brain Reasoning", "uni": "Google Research", "city": "Mountain View", "state": "California", "country": "US", "h": 45, "papers": 91, "topics": ["least-to-most prompting", "self-consistency", "compositional reasoning"]},
    {"id": "s182", "name": "Prof. Aman Madaan", "aff": "CMU LTI Reasoning", "uni": "Carnegie Mellon University", "city": "Pittsburgh", "state": "Pennsylvania", "country": "US", "h": 30, "papers": 50, "topics": ["self-refinement", "iterative feedback", "LLM self-improvement"]},

    # --- Vision Foundation Models ---
    {"id": "s183", "name": "Prof. Alexei Efros", "aff": "Berkeley Vision", "uni": "University of California, Berkeley", "city": "Berkeley", "state": "California", "country": "US", "h": 70, "papers": 170, "topics": ["visual self-supervision", "image analogies", "cross-domain transfer"]},
    {"id": "s184", "name": "Dr. Kaiming He", "aff": "MIT Vision FM", "uni": "Massachusetts Institute of Technology", "city": "Cambridge", "state": "Massachusetts", "country": "US", "h": 72, "papers": 175, "topics": ["masked autoencoders", "residual learning", "vision foundation models"]},
    {"id": "s185", "name": "Prof. Ross Girshick", "aff": "Meta FAIR Vision", "uni": "Meta AI Research", "city": "New York", "state": "New York", "country": "US", "h": 65, "papers": 148, "topics": ["object detection architectures", "instance segmentation", "feature pyramid networks"]},

    # --- Efficient Training ---
    {"id": "s186", "name": "Prof. Ce Zhang", "aff": "U Chicago Data", "uni": "University of Chicago", "city": "Chicago", "state": "Illinois", "country": "US", "h": 46, "papers": 94, "topics": ["data selection", "coreset methods", "efficient data loading"]},
    {"id": "s187", "name": "Dr. Samyam Rajbhandari", "aff": "Microsoft DeepSpeed", "uni": "Microsoft Research", "city": "Redmond", "state": "Washington", "country": "US", "h": 34, "papers": 57, "topics": ["ZeRO optimization", "DeepSpeed", "large-scale training"]},

    # --- Robotics (more) ---
    {"id": "s188", "name": "Prof. Pieter Abbeel", "aff": "Berkeley Robot", "uni": "University of California, Berkeley", "city": "Berkeley", "state": "California", "country": "US", "h": 63, "papers": 152, "topics": ["learning from demonstrations", "robot manipulation", "sim-to-real"]},
    {"id": "s189", "name": "Dr. Andy Zeng", "aff": "Google Robotics", "uni": "Google DeepMind", "city": "Mountain View", "state": "California", "country": "US", "h": 35, "papers": 60, "topics": ["language-conditioned robotics", "SayCan", "task and motion planning"]},

    # --- Diffusion Models ---
    {"id": "s190", "name": "Prof. Yang Song", "aff": "OpenAI Diffusion", "uni": "OpenAI", "city": "San Francisco", "state": "California", "country": "US", "h": 40, "papers": 75, "topics": ["score matching", "diffusion SDEs", "consistency models"]},
    {"id": "s191", "name": "Dr. Robin Rombach", "aff": "Stability Diffusion", "uni": "Stability AI", "city": "Munich", "state": "Bavaria", "country": "DE", "h": 32, "papers": 52, "topics": ["latent diffusion", "stable diffusion", "high-resolution synthesis"]},

    # --- Multimodal LLMs ---
    {"id": "s192", "name": "Prof. Chunyuan Li", "aff": "Microsoft MM", "uni": "Microsoft Research", "city": "Redmond", "state": "Washington", "country": "US", "h": 44, "papers": 88, "topics": ["multimodal LLMs", "visual instruction tuning", "LLaVA"]},
    {"id": "s193", "name": "Dr. Haotian Liu", "aff": "UW Multimodal LLM", "uni": "University of Wisconsin-Madison", "city": "Madison", "state": "Wisconsin", "country": "US", "h": 28, "papers": 43, "topics": ["visual chat", "multimodal instruction following", "image understanding LLMs"]},

    # --- Reasoning & Planning ---
    {"id": "s194", "name": "Prof. Karthik Narasimhan", "aff": "Princeton Planning", "uni": "Princeton University", "city": "Princeton", "state": "New Jersey", "country": "US", "h": 36, "papers": 64, "topics": ["language model planning", "grounded language understanding", "interactive environments"]},
    {"id": "s195", "name": "Dr. Yejin Choi", "aff": "UW Commonsense", "uni": "University of Washington", "city": "Seattle", "state": "Washington", "country": "US", "h": 60, "papers": 143, "topics": ["commonsense reasoning", "moral reasoning", "abductive NLG"]},

    # --- More ML ---
    {"id": "s196", "name": "Prof. Ludwig Schmidt", "aff": "UW Robust ML", "uni": "University of Washington", "city": "Seattle", "state": "Washington", "country": "US", "h": 40, "papers": 78, "topics": ["distribution shift", "CLIP benchmarks", "dataset design"]},
    {"id": "s197", "name": "Dr. Jonas Peters", "aff": "Copenhagen Causal", "uni": "University of Copenhagen", "city": "Copenhagen", "state": "Hovedstaden", "country": "DK", "h": 42, "papers": 82, "topics": ["causal representation learning", "invariant prediction", "causal models"]},
    {"id": "s198", "name": "Prof. Tengyu Ma", "aff": "Stanford Theory ML", "uni": "Stanford University", "city": "Stanford", "state": "California", "country": "US", "h": 43, "papers": 85, "topics": ["pretraining theory", "in-context learning theory", "transformers theory"]},
    {"id": "s199", "name": "Dr. Sara Hooker", "aff": "Cohere For AI", "uni": "Cohere For AI", "city": "Toronto", "state": "Ontario", "country": "CA", "h": 31, "papers": 50, "topics": ["model pruning fairness", "compression bias", "efficient model evaluation"]},
    {"id": "s200", "name": "Prof. Percy Liang", "aff": "Stanford CRFM", "uni": "Stanford University", "city": "Stanford", "state": "California", "country": "US", "h": 65, "papers": 160, "topics": ["foundation model evaluation", "HELM benchmark", "responsible AI deployment"]},
]


def _build_scholars() -> list[ScholarCard]:
    """Convert raw dicts into ScholarCard objects with randomized scores."""
    rng = random.Random(42)  # deterministic
    scholars = []
    for s in _RAW_SCHOLARS:
        jac = round(rng.uniform(0.45, 0.95), 2)
        sem = round(rng.uniform(0.60, 0.98), 2)
        cit = round(rng.uniform(0.30, 0.92), 2)
        score = round(0.2 * jac + 0.6 * sem + 0.2 * cit, 2)
        scholars.append(ScholarCard(
            scholar_id=s["id"],
            name=s["name"],
            affiliation=s["aff"],
            university=s["uni"],
            city=s["city"],
            state=s["state"],
            country=s["country"],
            h_index=s["h"],
            paper_count=s["papers"],
            topics=s["topics"],
            score=score,
            score_breakdown=ScoreBreakdown(jaccard=jac, semantic=sem, citation=cit),
            match_explanation=(
                f"{s['name']}'s expertise in {s['topics'][0]} and {s['topics'][1]} "
                f"is highly relevant to your research query."
            ),
        ))
    return scholars


MOCK_SCHOLARS: list[ScholarCard] = _build_scholars()

# Build lookup for fast access by ID
SCHOLAR_BY_ID: dict[str, ScholarCard] = {s.scholar_id: s for s in MOCK_SCHOLARS}

# ---------------------------------------------------------------------------
# Topic keyword → scholar field mapping for intelligent search
# ---------------------------------------------------------------------------
FIELD_KEYWORDS: dict[str, list[str]] = {
    "machine learning": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s86", "s87", "s88", "s89"],
    "ML": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s86", "s87", "s88", "s89"],
    "natural language processing": ["s11", "s12", "s13", "s14", "s15", "s16", "s17", "s18", "s19", "s20", "s81", "s82", "s83", "s84", "s85", "s134", "s135", "s136", "s137", "s138"],
    "NLP": ["s11", "s12", "s13", "s14", "s15", "s16", "s17", "s18", "s19", "s20", "s81", "s82", "s83", "s84", "s85", "s134", "s135", "s136", "s137", "s138"],
    "computer vision": ["s21", "s22", "s23", "s24", "s25", "s26", "s27", "s28", "s29", "s30", "s76", "s77", "s78", "s79", "s80", "s139", "s140", "s141", "s142"],
    "CV": ["s21", "s22", "s23", "s24", "s25", "s26", "s27", "s28", "s29", "s30", "s76", "s77", "s78", "s79", "s80", "s139", "s140", "s141", "s142"],
    "reinforcement learning": ["s31", "s32", "s33", "s34", "s35", "s36", "s37", "s38", "s168", "s169"],
    "RL": ["s31", "s32", "s33", "s34", "s35", "s36", "s37", "s38", "s168", "s169"],
    "robotics": ["s39", "s40", "s41", "s42", "s43", "s44", "s45", "s188", "s189"],
    "graph neural networks": ["s46", "s47", "s48", "s49", "s50"],
    "GNN": ["s46", "s47", "s48", "s49", "s50"],
    "generative AI": ["s51", "s52", "s53", "s54", "s55", "s56", "s57", "s190", "s191"],
    "diffusion": ["s51", "s26", "s54", "s190", "s191"],
    "speech": ["s58", "s59", "s60", "s61"],
    "information retrieval": ["s62", "s63", "s64", "s65", "s166", "s167"],
    "retrieval": ["s62", "s63", "s64", "s65", "s166", "s167"],
    "AI for science": ["s66", "s67", "s68", "s69", "s70"],
    "drug discovery": ["s49", "s50", "s66", "s68"],
    "safety": ["s71", "s72", "s73", "s74", "s75"],
    "alignment": ["s71", "s72", "s34"],
    "multimodal": ["s94", "s95", "s96", "s97", "s192", "s193"],
    "self-supervised": ["s98", "s99", "s100"],
    "LLM": ["s13", "s150", "s151", "s152", "s155", "s156", "s157", "s158", "s180", "s181", "s182", "s192", "s193", "s200"],
    "large language model": ["s13", "s150", "s151", "s152", "s155", "s156", "s157", "s158", "s180", "s181", "s182", "s192", "s193", "s200"],
    "efficient": ["s3", "s119", "s120", "s121", "s155", "s156", "s157", "s158"],
    "autonomous driving": ["s41", "s143", "s144", "s145"],
    "healthcare": ["s159", "s160", "s161"],
    "medical": ["s28", "s159", "s160", "s161"],
    "climate": ["s122", "s123", "s124"],
    "federated learning": ["s8", "s170", "s171"],
    "meta-learning": ["s128", "s129", "s130"],
    "reasoning": ["s180", "s181", "s182", "s194", "s195"],
    "agents": ["s150", "s151", "s152"],
}


# ---------------------------------------------------------------------------
# Graph & Ideas (kept simple)
# ---------------------------------------------------------------------------

MOCK_GRAPH_NODES: list[GraphNode] = [
    GraphNode(id="user", label="You", type="user"),
    GraphNode(id="t1", label="KV cache compression", type="topic"),
    GraphNode(id="t2", label="efficient transformers", type="topic"),
    GraphNode(id="t3", label="model compression", type="topic"),
    GraphNode(id="s1", label="Dr. Amara Osei", type="scholar"),
    GraphNode(id="s2", label="Prof. Liang Chen", type="scholar"),
    GraphNode(id="s3", label="Dr. Sofia Rodriguez", type="scholar"),
    GraphNode(id="p1", label="Efficient KV Cache Eviction (2024)", type="paper"),
    GraphNode(id="i1", label="MIT CSAIL", type="institution"),
]

MOCK_GRAPH_EDGES: list[GraphEdge] = [
    GraphEdge(source="user", target="t1", weight=1.0, reason="searched for this topic"),
    GraphEdge(source="t1", target="s1", weight=0.93, reason="top match on KV cache compression"),
    GraphEdge(source="t2", target="s2", weight=0.88, reason="top match on efficient transformers"),
    GraphEdge(source="t3", target="s3", weight=0.82, reason="top match on model compression"),
    GraphEdge(source="s1", target="p1", weight=1.0, reason="authored this paper"),
    GraphEdge(source="s1", target="i1", weight=1.0, reason="affiliated with MIT CSAIL"),
    GraphEdge(source="s1", target="s2", weight=0.45, reason="3 shared citations"),
]

MOCK_PROJECT_IDEAS: list[ProjectIdea] = [
    ProjectIdea(
        title="Adaptive KV Cache Compression for Multi-Turn Dialogue",
        description="Combine Dr. Osei's eviction policies with Prof. Chen's long-context attention to build a cache that adapts its compression ratio based on conversation turn depth.",
        suggested_venues=["NeurIPS", "ICML", "MLSys"],
        skill_gap="Dr. Osei brings systems-level KV cache expertise; Prof. Chen contributes attention mechanism theory; you bridge with multi-turn inference benchmarks.",
    ),
    ProjectIdea(
        title="Edge-Deployable Sparse Transformer with Dynamic MoE Routing",
        description="Merge Dr. Rodriguez's quantization techniques with Dr. Tanaka's MoE routing to create a model that runs on consumer GPUs with minimal quality loss.",
        suggested_venues=["EMNLP", "ACL", "ICLR"],
        skill_gap="Dr. Rodriguez handles compression/quantization; Dr. Tanaka designs MoE routing; you evaluate end-to-end latency and quality tradeoffs.",
    ),
    ProjectIdea(
        title="Speculative Decoding Meets KV Cache Sharing",
        description="Use Prof. Patel's speculative decoding framework with a shared KV cache pool across draft and target models, reducing memory overhead by up to 40%.",
        suggested_venues=["MLSys", "OSDI", "ASPLOS"],
        skill_gap="Prof. Patel provides speculative decoding infra; you contribute KV cache optimization; jointly develop the shared-cache protocol.",
    ),
]

MOCK_CHAT_REPLIES: dict[str, str] = {
    "default": "Based on the research profiles of the scholars in this session, I can see several promising areas of overlap. Their combined expertise spans KV cache optimization, efficient attention mechanisms, and model compression — a powerful combination for tackling inference efficiency at scale. What specific aspect would you like to explore?",
    "project": "Here are some collaboration angles I see:\n\n1. **Adaptive Cache Management** — Combining eviction policies with long-context attention\n2. **Compression-Aware Serving** — Integrating quantization into the serving stack\n3. **Hybrid Speculative Decoding** — Using sparse MoE models as draft models\n\nWould you like me to elaborate on any of these?",
    "email": "Here's a draft outreach email:\n\n---\n\nSubject: Potential Collaboration on Inference Optimization\n\nDear Dr. Osei,\n\nI've been following your recent work on KV cache eviction policies with great interest. My research focuses on [your area], and I believe there's a compelling intersection between our approaches...\n\n---\n\nWould you like me to customize this further?",
}
