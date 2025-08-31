"""
持久化管理器
负责系统数据的保存和加载
"""

import os
import json
import pickle
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)

class PersistenceManager:
    """持久化管理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.cache_dir = self.data_dir / "cache"
        self.backup_dir = self.data_dir / "backup"
        self.interactions_dir = self.data_dir / "interactions"
        self.agent_profiles_dir = self.data_dir / "agent_profiles"
        
        # 创建必要的目录
        self._ensure_directories()
        
        # 持久化配置
        self.auto_save_interval = 300  # 5分钟自动保存
        self.backup_retention_days = 7  # 备份保留7天
        self.max_interaction_files = 100  # 最多保留100个交互文件
        
        # 线程控制
        self._auto_save_thread = None
        self._shutdown_event = threading.Event()
        self._save_lock = threading.RLock()
        
        # 数据缓存
        self._cached_data = {}
        self._last_save_time = {}
        
        logger.info(f"持久化管理器初始化完成，数据目录: {self.data_dir}")
    
    def _ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [
            self.data_dir,
            self.cache_dir,
            self.backup_dir,
            self.interactions_dir,
            self.agent_profiles_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"确保目录存在: {directory}")
    
    def start_auto_save(self, system_data_getter):
        """启动自动保存线程"""
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            logger.warning("自动保存线程已在运行")
            return
        
        self._auto_save_thread = threading.Thread(
            target=self._auto_save_loop,
            args=(system_data_getter,),
            name="AutoSave",
            daemon=True
        )
        self._auto_save_thread.start()
        logger.info("自动保存线程已启动")
    
    def _auto_save_loop(self, system_data_getter):
        """自动保存循环"""
        while not self._shutdown_event.is_set():
            try:
                # 等待保存间隔
                if self._shutdown_event.wait(self.auto_save_interval):
                    break
                
                # 获取系统数据并保存
                system_data = system_data_getter()
                if system_data:
                    self.save_system_state(system_data)
                    logger.info("自动保存完成")
                
            except Exception as e:
                logger.error(f"自动保存失败: {e}")
    
    def save_system_state(self, system_data: Dict[str, Any], quick_mode: bool = False) -> bool:
        """保存完整的系统状态
        
        Args:
            system_data: 系统数据
            quick_mode: 快速模式，只保存关键数据
        """
        try:
            with self._save_lock:
                timestamp = datetime.now()
                
                # 保存各个组件的数据
                success_count = 0
                total_count = 0
                
                # 快速模式只保存关键数据
                if quick_mode:
                    # 只保存Agent位置和社交网络
                    if 'agents' in system_data:
                        total_count += 1
                        if self._save_agent_states(system_data['agents'], timestamp):
                            success_count += 1
                    
                    if 'social_network' in system_data:
                        total_count += 1 
                        if self._save_social_network(system_data['social_network'], timestamp):
                            success_count += 1
                    
                    if 'config' in system_data:
                        total_count += 1
                        if self._save_system_config(system_data['config'], timestamp):
                            success_count += 1
                            
                    logger.info(f"快速保存完成: {success_count}/{total_count} 组件成功保存")
                    return success_count == total_count
                
                # 完整模式保存所有数据
                # 1. Agent状态
                if 'agents' in system_data:
                    total_count += 1
                    if self._save_agent_states(system_data['agents'], timestamp):
                        success_count += 1
                
                # 2. 社交网络
                if 'social_network' in system_data:
                    total_count += 1
                    if self._save_social_network(system_data['social_network'], timestamp):
                        success_count += 1
                
                # 3. 建筑物状态
                if 'buildings' in system_data:
                    total_count += 1
                    if self._save_buildings_state(system_data['buildings'], timestamp):
                        success_count += 1
                
                # 4. 聊天历史
                if 'chat_history' in system_data:
                    total_count += 1
                    if self._save_chat_history(system_data['chat_history'], timestamp):
                        success_count += 1
                
                # 5. 系统配置
                if 'config' in system_data:
                    total_count += 1
                    if self._save_system_config(system_data['config'], timestamp):
                        success_count += 1
                
                # 6. 内存数据
                if 'memory_data' in system_data:
                    total_count += 1
                    if self._save_memory_data(system_data['memory_data'], timestamp):
                        success_count += 1
                
                # 创建快照
                self._create_system_snapshot(system_data, timestamp)
                
                logger.info(f"系统状态保存完成: {success_count}/{total_count} 组件成功保存")
                return success_count == total_count
                
        except Exception as e:
            logger.error(f"保存系统状态失败: {e}")
            return False
    
    def _save_agent_states(self, agents: Dict, timestamp: datetime) -> bool:
        """保存Agent状态"""
        try:
            agent_data = {}
            for name, agent in agents.items():
                # 确保保存完整的Agent数据
                agent_info = {
                    'name': getattr(agent, 'name', name),
                    'profession': getattr(agent, 'profession', '通用'),
                    'location': getattr(agent, 'location', '家'),
                    'emoji': getattr(agent, 'emoji', '🤖'),
                    'energy_level': getattr(agent, 'energy_level', 80),
                    'current_mood': getattr(agent, 'current_mood', '平静'),
                    'interaction_count': getattr(agent, 'interaction_count', 0),
                    'last_interaction_time': getattr(agent, 'last_interaction_time', None),
                    'last_updated': timestamp.isoformat()
                }
                
                # 如果Agent有real_agent，也保存其属性
                if hasattr(agent, 'real_agent') and agent.real_agent:
                    real_agent = agent.real_agent
                    agent_info.update({
                        'real_agent_name': getattr(real_agent, 'name', name),
                        'real_agent_profession': getattr(real_agent, 'profession', '通用'),
                        'real_agent_location': getattr(real_agent, 'current_location', '家')
                    })
                
                agent_data[name] = agent_info
            
            file_path = self.cache_dir / "agent_states.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(agent_data, f, ensure_ascii=False, indent=2)
            
            # 同时保存到agent_profiles目录
            for name, data in agent_data.items():
                profile_file = self.agent_profiles_dir / f"{name}.json"
                with open(profile_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"保存Agent状态失败: {e}")
            return False
    
    def _save_social_network(self, social_network: Any, timestamp: datetime) -> bool:
        """保存社交网络数据"""
        try:
            # 提取社交网络数据
            network_data = {
                'relationships': {},
                'interaction_history': [],
                'last_updated': timestamp.isoformat()
            }
            
            # 如果social_network有get_all_relationships方法
            if hasattr(social_network, 'get_all_relationships'):
                network_data['relationships'] = social_network.get_all_relationships()
            
            # 如果有交互历史
            if hasattr(social_network, 'interaction_history'):
                network_data['interaction_history'] = social_network.interaction_history[-1000:]  # 保留最近1000条
            
            file_path = self.cache_dir / "social_network.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(network_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"保存社交网络失败: {e}")
            return False
    
    def _save_buildings_state(self, buildings: Dict, timestamp: datetime) -> bool:
        """保存建筑物状态"""
        try:
            # 创建可序列化的建筑物数据
            buildings_data = {}
            for name, building in buildings.items():
                buildings_data[name] = {
                    'name': name,
                    'x': building.get('x', 0),
                    'y': building.get('y', 0),
                    'emoji': building.get('emoji', '🏢'),
                    'occupants': list(building.get('occupants', [])),
                    'last_updated': timestamp.isoformat()
                }
            
            file_path = self.cache_dir / "buildings_state.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(buildings_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"保存建筑物状态失败: {e}")
            return False
    
    def _save_chat_history(self, chat_history: List, timestamp: datetime) -> bool:
        """保存聊天历史"""
        try:
            # 限制聊天历史长度
            limited_history = chat_history[-500:] if len(chat_history) > 500 else chat_history
            
            chat_data = {
                'history': limited_history,
                'total_count': len(chat_history),
                'last_updated': timestamp.isoformat()
            }
            
            file_path = self.cache_dir / "chat_history.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"保存聊天历史失败: {e}")
            return False
    
    def _save_system_config(self, config: Dict, timestamp: datetime) -> bool:
        """保存系统配置"""
        try:
            config_data = {
                **config,
                'last_updated': timestamp.isoformat(),
                'persistence_config': {
                    'auto_save_interval': self.auto_save_interval,
                    'backup_retention_days': self.backup_retention_days,
                    'max_interaction_files': self.max_interaction_files
                }
            }
            
            file_path = self.cache_dir / "system_config.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"保存系统配置失败: {e}")
            return False
    
    def _save_memory_data(self, memory_data: Any, timestamp: datetime) -> bool:
        """保存内存数据"""
        try:
            # 根据内存管理器类型保存数据
            memory_info = {
                'type': type(memory_data).__name__,
                'last_updated': timestamp.isoformat()
            }
            
            # 如果是向量存储相关的内存数据
            if hasattr(memory_data, 'vector_store'):
                vector_store = memory_data.vector_store
                
                # 保存向量数据库连接状态
                connection_status = vector_store.get_connection_status()
                memory_info['vector_db_status'] = connection_status
                
                # 如果连接正常，保存统计信息
                if connection_status.get('connected', False):
                    try:
                        collections = vector_store.client.get_collections()
                        collections_stats = {}
                        
                        for collection in collections.collections:
                            try:
                                stats = vector_store.get_collection_stats(collection.name)
                                collections_stats[collection.name] = stats
                            except Exception as e:
                                logger.warning(f"获取集合 {collection.name} 统计失败: {e}")
                        
                        memory_info['collections_stats'] = collections_stats
                        
                        # 保存向量数据库备份信息（如果需要）
                        self._backup_vector_database_metadata(collections_stats, timestamp)
                        
                    except Exception as e:
                        logger.warning(f"保存向量数据库统计失败: {e}")
            
            # 保存到文件
            file_path = self.cache_dir / "memory_data.json" 
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(memory_info, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"保存内存数据失败: {e}")
            return False
    
    def _backup_vector_database_metadata(self, collections_stats: Dict, timestamp: datetime):
        """备份向量数据库元数据"""
        try:
            backup_data = {
                'timestamp': timestamp.isoformat(),
                'collections_stats': collections_stats,
                'backup_type': 'vector_db_metadata'
            }
            
            # 创建备份文件
            backup_filename = f"vector_db_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = self.backup_dir / backup_filename
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"向量数据库元数据备份完成: {backup_filename}")
            
        except Exception as e:
            logger.warning(f"备份向量数据库元数据失败: {e}")
    
    def _create_system_snapshot(self, system_data: Dict, timestamp: datetime):
        """创建系统快照"""
        try:
            snapshot_data = {
                'timestamp': timestamp.isoformat(),
                'version': '1.0',
                'components': list(system_data.keys()),
                'agent_count': len(system_data.get('agents', {})),
                'building_count': len(system_data.get('buildings', {})),
                'chat_messages': len(system_data.get('chat_history', [])),
            }
            
            snapshot_file = self.backup_dir / f"snapshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
            
            # 清理旧快照
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"创建系统快照失败: {e}")
    
    def load_system_state(self) -> Dict[str, Any]:
        """加载完整的系统状态"""
        try:
            with self._save_lock:
                loaded_data = {}
                
                # 加载各个组件
                loaded_data['agents'] = self._load_agent_states()
                loaded_data['social_network'] = self._load_social_network()
                loaded_data['buildings'] = self._load_buildings_state()
                loaded_data['chat_history'] = self._load_chat_history()
                loaded_data['config'] = self._load_system_config()
                loaded_data['memory_data'] = self._load_memory_data()
                
                logger.info("系统状态加载完成")
                return loaded_data
                
        except Exception as e:
            logger.error(f"加载系统状态失败: {e}")
            return {}
    
    def _load_agent_states(self) -> Dict:
        """加载Agent状态"""
        try:
            file_path = self.cache_dir / "agent_states.json"
            if not file_path.exists():
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载Agent状态失败: {e}")
            return {}
    
    def _load_social_network(self) -> Dict:
        """加载社交网络数据"""
        try:
            file_path = self.cache_dir / "social_network.json"
            if not file_path.exists():
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载社交网络失败: {e}")
            return {}
    
    def _load_buildings_state(self) -> Dict:
        """加载建筑物状态"""
        try:
            file_path = self.cache_dir / "buildings_state.json"
            if not file_path.exists():
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载建筑物状态失败: {e}")
            return {}
    
    def _load_chat_history(self) -> List:
        """加载聊天历史"""
        try:
            file_path = self.cache_dir / "chat_history.json"
            if not file_path.exists():
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('history', [])
        except Exception as e:
            logger.error(f"加载聊天历史失败: {e}")
            return []
    
    def _load_system_config(self) -> Dict:
        """加载系统配置"""
        try:
            file_path = self.cache_dir / "system_config.json"
            if not file_path.exists():
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载系统配置失败: {e}")
            return {}
    
    def _load_memory_data(self) -> Dict:
        """加载内存数据"""
        try:
            file_path = self.cache_dir / "memory_data.json"
            if not file_path.exists():
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载内存数据失败: {e}")
            return {}
    
    def _cleanup_old_backups(self):
        """清理旧备份文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
            
            for backup_file in self.backup_dir.glob("snapshot_*.json"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    logger.debug(f"删除旧备份: {backup_file}")
                    
        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")
    
    def save_interaction(self, interaction_data: Dict) -> bool:
        """保存单个交互记录"""
        try:
            timestamp = datetime.now()
            interaction_file = self.interactions_dir / f"interaction_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
            
            interaction_record = {
                **interaction_data,
                'saved_at': timestamp.isoformat()
            }
            
            with open(interaction_file, 'w', encoding='utf-8') as f:
                json.dump(interaction_record, f, ensure_ascii=False, indent=2)
            
            # 清理旧交互文件
            self._cleanup_old_interactions()
            
            return True
            
        except Exception as e:
            logger.error(f"保存交互记录失败: {e}")
            return False
    
    def _cleanup_old_interactions(self):
        """清理旧交互文件"""
        try:
            interaction_files = sorted(
                self.interactions_dir.glob("interaction_*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            
            # 保留最新的文件
            for old_file in interaction_files[self.max_interaction_files:]:
                old_file.unlink()
                logger.debug(f"删除旧交互文件: {old_file}")
                
        except Exception as e:
            logger.error(f"清理旧交互文件失败: {e}")
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            stats = {
                'data_directory': str(self.data_dir),
                'cache_files': len(list(self.cache_dir.glob("*.json"))),
                'backup_files': len(list(self.backup_dir.glob("*.json"))),
                'interaction_files': len(list(self.interactions_dir.glob("*.json"))),
                'agent_profiles': len(list(self.agent_profiles_dir.glob("*.json"))),
                'auto_save_enabled': self._auto_save_thread and self._auto_save_thread.is_alive(),
                'last_save_times': self._last_save_time.copy()
            }
            
            # 计算数据目录大小
            total_size = sum(f.stat().st_size for f in self.data_dir.rglob("*.json"))
            stats['total_data_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def shutdown(self):
        """关闭持久化管理器"""
        logger.info("开始关闭持久化管理器...")
        
        # 停止自动保存线程
        self._shutdown_event.set()
        
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            self._auto_save_thread.join(timeout=5.0)
        
        logger.info("持久化管理器已关闭")
