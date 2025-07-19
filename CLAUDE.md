# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Membase is a decentralized AI memory layer Python SDK that provides:
- Persistent conversation storage for AI agents
- Scalable knowledge bases using vector storage (ChromaDB)
- Secure on-chain collaboration between agents
- Blockchain-based identity management and task coordination

## Development Commands

### Running Tests
```bash
# Run all tests
python -m unittest discover tests/

# Run specific test modules
python -m unittest tests.test_memory
python -m unittest tests.test_multi_memory
python -m unittest tests.test_chroma
python -m unittest tests.test_chain
python -m unittest tests.test_beeper
python -m unittest tests.test_trader
python -m unittest tests.test_load

# Run individual test files directly
python tests/test_memory.py
```

### Building and Installation
```bash
# Install in development mode
pip install -e .

# Build distribution packages
python -m build

# Install dependencies
pip install chromadb>=0.6.3 loguru>=0.7.3 requests>=2.32.3 web3>=7.8.0
```

## Architecture Overview

### Module Structure
- **membase.memory**: Conversation memory management
  - `BufferedMemory`: Single conversation thread storage
  - `MultiMemory`: Multiple conversation management with hub integration
  - `Message`: Core message model with role, content, and metadata

- **membase.knowledge**: Vector storage for RAG
  - `ChromaKnowledgeBase`: ChromaDB integration for document storage
  - `Document`: Document model with content and metadata
  - Supports add, update, delete, query operations

- **membase.chain**: Blockchain integration
  - `membase_chain`: Main blockchain interface singleton
  - Agent registration and authentication
  - Task creation, joining, and settlement
  - Buy/sell permissions between agents

- **membase.storage**: Decentralized storage
  - `Hub`: Integration with Membase Hub for persistence
  - Auto-upload and preload capabilities

### Key Design Patterns

1. **Singleton Chain Interface**: The `membase_chain` object is a global singleton that manages all blockchain interactions.

2. **Auto-Upload Pattern**: Both memory and knowledge modules support `auto_upload_to_hub=True` for automatic synchronization.

3. **Preload Support**: Memory modules can preload existing data from hub with `preload_from_hub=True`.

4. **Environment Configuration**: Uses environment variables for identity:
   - `MEMBASE_ID`: Unique agent identifier
   - `MEMBASE_ACCOUNT`: Blockchain account address
   - `MEMBASE_SECRET_KEY`: Account private key

### Testing Approach

Tests use `unittest.mock` extensively to mock external dependencies:
- Web3 blockchain calls are mocked
- HTTP requests to storage hub are mocked
- ChromaDB operations are partially mocked

When adding new features, follow the existing test patterns in the respective test files.

### Smart Contract Integration

The project includes compiled Solidity contracts in `src/membase/chain/solc/`:
- Beeper.sol: Main contract for agent and task management
- BeeperToken.sol: Token implementation for staking
- Integration with Pancake V3 for liquidity

Contract ABIs are loaded from JSON files and used with web3.py for blockchain interactions.

## Important Considerations

1. **Blockchain Network**: Currently configured for BSC testnet (Chain ID: 97)
2. **Storage Hub**: Located at https://testnet.storage.unibase.site
3. **Explorer**: Web interface at https://testnet.explorer.unibase.com/
4. **Python Version**: Requires Python 3.10+
5. **No Linting/Formatting**: Project has no configured linting or formatting tools