"""
监控指标收集模块

收集系统性能指标、业务指标和用户行为数据。
"""

import time
import psutil
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import structlog
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest

from .config import get_config
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class MetricPoint:
    """指标数据点"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


class MetricsCollector:
    """
    监控指标收集器

    收集系统性能、业务指标和用户行为数据。
    """

    def __init__(self):
        self.config = get_config()

        # Prometheus注册表
        self.registry = CollectorRegistry()

        # 系统指标
        self.cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'CPU使用率',
            registry=self.registry
        )
        self.memory_usage = Gauge(
            'system_memory_usage_percent',
            '内存使用率',
            registry=self.registry
        )
        self.disk_usage = Gauge(
            'system_disk_usage_percent',
            '磁盘使用率',
            registry=self.registry
        )

        # 业务指标
        self.query_counter = Counter(
            'rag_queries_total',
            'RAG查询总数',
            ['user_id', 'knowledge_base_id', 'mode', 'status'],
            registry=self.registry
        )
        self.query_duration = Histogram(
            'rag_query_duration_seconds',
            'RAG查询响应时间',
            ['mode', 'knowledge_base_id'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
            registry=self.registry
        )
        self.retrieval_duration = Histogram(
            'rag_retrieval_duration_seconds',
            '检索时间',
            ['mode'],
            registry=self.registry
        )
        self.generation_duration = Histogram(
            'rag_generation_duration_seconds',
            '生成时间',
            registry=self.registry
        )

        # 知识库指标
        self.documents_count = Gauge(
            'knowledge_base_documents_total',
            '知识库文档总数',
            ['knowledge_base_id'],
            registry=self.registry
        )
        self.chunks_count = Gauge(
            'knowledge_base_chunks_total',
            '知识库文档块总数',
            ['knowledge_base_id'],
            registry=self.registry
        )
        self.entities_count = Gauge(
            'knowledge_base_entities_total',
            '知识库实体总数',
            ['knowledge_base_id'],
            registry=self.registry
        )

        # 用户指标
        self.active_users = Gauge(
            'active_users_total',
            '活跃用户数',
            registry=self.registry
        )
        self.user_sessions = Gauge(
            'user_sessions_total',
            '用户会话数',
            registry=self.registry
        )

        # 错误指标
        self.error_counter = Counter(
            'errors_total',
            '错误总数',
            ['error_type', 'component'],
            registry=self.registry
        )

        # 缓存指标
        self.cache_hits = Counter(
            'cache_hits_total',
            '缓存命中次数',
            ['cache_type'],
            registry=self.registry
        )
        self.cache_misses = Counter(
            'cache_misses_total',
            '缓存未命中次数',
            ['cache_type'],
            registry=self.registry
        )

        # 内存中的指标存储
        self._metrics_buffer: List[MetricPoint] = []
        self._max_buffer_size = 10000

        logger.info("指标收集器初始化完成")

    async def collect_system_metrics(self) -> Dict[str, float]:
        """
        收集系统指标

        Returns:
            系统指标字典
        """
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.set(cpu_percent)

            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.memory_usage.set(memory_percent)

            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.disk_usage.set(disk_percent)

            # 网络统计
            net_io = psutil.net_io_counters()

            metrics = {
                'cpu_usage': cpu_percent,
                'memory_usage': memory_percent,
                'memory_total': memory.total,
                'memory_available': memory.available,
                'disk_usage': disk_percent,
                'disk_total': disk.total,
                'disk_free': disk.free,
                'network_bytes_sent': net_io.bytes_sent,
                'network_bytes_recv': net_io.bytes_recv,
                'timestamp': time.time()
            }

            # 添加到缓冲区
            for name, value in metrics.items():
                if name != 'timestamp':
                    self._add_metric_point(
                        MetricPoint(
                            name=f"system_{name}",
                            value=float(value),
                            timestamp=datetime.utcnow(),
                            labels={"type": "system"}
                        )
                    )

            logger.debug("系统指标收集完成", metrics=metrics)
            return metrics

        except Exception as e:
            logger.error("系统指标收集失败", error=str(e))
            self.record_error("system_metrics", "metrics_collector")
            return {}

    def record_query(
        self,
        user_id: str,
        knowledge_base_id: str,
        mode: str,
        duration: float,
        status: str = "success"
    ) -> None:
        """
        记录查询指标

        Args:
            user_id: 用户ID
            knowledge_base_id: 知识库ID
            mode: 检索模式
            duration: 查询时长
            status: 查询状态
        """
        try:
            # 更新计数器
            self.query_counter.labels(
                user_id=user_id,
                knowledge_base_id=knowledge_base_id,
                mode=mode,
                status=status
            ).inc()

            # 记录响应时间
            self.query_duration.labels(
                mode=mode,
                knowledge_base_id=knowledge_base_id
            ).observe(duration)

            # 添加到缓冲区
            self._add_metric_point(
                MetricPoint(
                    name="rag_query",
                    value=duration,
                    timestamp=datetime.utcnow(),
                    labels={
                        "user_id": user_id,
                        "knowledge_base_id": knowledge_base_id,
                        "mode": mode,
                        "status": status
                    },
                    unit="seconds"
                )
            )

            logger.debug(
                "查询指标记录完成",
                user_id=user_id,
                kb_id=knowledge_base_id,
                mode=mode,
                duration=duration,
                status=status
            )

        except Exception as e:
            logger.error("记录查询指标失败", error=str(e))

    def record_retrieval(self, mode: str, duration: float) -> None:
        """
        记录检索指标

        Args:
            mode: 检索模式
            duration: 检索时长
        """
        try:
            self.retrieval_duration.labels(mode=mode).observe(duration)

            self._add_metric_point(
                MetricPoint(
                    name="rag_retrieval",
                    value=duration,
                    timestamp=datetime.utcnow(),
                    labels={"mode": mode},
                    unit="seconds"
                )
            )

        except Exception as e:
            logger.error("记录检索指标失败", error=str(e))

    def record_generation(self, duration: float, tokens_used: int = 0) -> None:
        """
        记录生成指标

        Args:
            duration: 生成时长
            tokens_used: 使用的Token数量
        """
        try:
            self.generation_duration.observe(duration)

            self._add_metric_point(
                MetricPoint(
                    name="rag_generation",
                    value=duration,
                    timestamp=datetime.utcnow(),
                    labels={"tokens_used": str(tokens_used)},
                    unit="seconds"
                )
            )

        except Exception as e:
            logger.error("记录生成指标失败", error=str(e))

    def update_knowledge_base_stats(
        self,
        knowledge_base_id: str,
        documents: int = 0,
        chunks: int = 0,
        entities: int = 0
    ) -> None:
        """
        更新知识库统计

        Args:
            knowledge_base_id: 知识库ID
            documents: 文档数量
            chunks: 文档块数量
            entities: 实体数量
        """
        try:
            if documents > 0:
                self.documents_count.labels(
                    knowledge_base_id=knowledge_base_id
                ).set(documents)

            if chunks > 0:
                self.chunks_count.labels(
                    knowledge_base_id=knowledge_base_id
                ).set(chunks)

            if entities > 0:
                self.entities_count.labels(
                    knowledge_base_id=knowledge_base_id
                ).set(entities)

            logger.debug(
                "知识库统计更新完成",
                kb_id=knowledge_base_id,
                documents=documents,
                chunks=chunks,
                entities=entities
            )

        except Exception as e:
            logger.error("更新知识库统计失败", error=str(e))

    def update_user_stats(self, active_users: int, sessions: int) -> None:
        """
        更新用户统计

        Args:
            active_users: 活跃用户数
            sessions: 会话数
        """
        try:
            self.active_users.set(active_users)
            self.user_sessions.set(sessions)

            self._add_metric_point(
                MetricPoint(
                    name="active_users",
                    value=float(active_users),
                    timestamp=datetime.utcnow(),
                    labels={"type": "user_stats"}
                )
            )

        except Exception as e:
            logger.error("更新用户统计失败", error=str(e))

    def record_error(self, error_type: str, component: str) -> None:
        """
        记录错误

        Args:
            error_type: 错误类型
            component: 组件名称
        """
        try:
            self.error_counter.labels(
                error_type=error_type,
                component=component
            ).inc()

            self._add_metric_point(
                MetricPoint(
                    name="error_occurred",
                    value=1.0,
                    timestamp=datetime.utcnow(),
                    labels={
                        "error_type": error_type,
                        "component": component
                    }
                )
            )

        except Exception as e:
            logger.error("记录错误指标失败", error=str(e))

    def record_cache_access(self, cache_type: str, hit: bool) -> None:
        """
        记录缓存访问

        Args:
            cache_type: 缓存类型
            hit: 是否命中
        """
        try:
            if hit:
                self.cache_hits.labels(cache_type=cache_type).inc()
            else:
                self.cache_misses.labels(cache_type=cache_type).inc()

            self._add_metric_point(
                MetricPoint(
                    name="cache_access",
                    value=1.0 if hit else 0.0,
                    timestamp=datetime.utcnow(),
                    labels={
                        "cache_type": cache_type,
                        "result": "hit" if hit else "miss"
                    }
                )
            )

        except Exception as e:
            logger.error("记录缓存指标失败", error=str(e))

    def _add_metric_point(self, metric: MetricPoint) -> None:
        """
        添加指标点到缓冲区

        Args:
            metric: 指标点
        """
        self._metrics_buffer.append(metric)

        # 如果缓冲区满了，移除最旧的指标
        if len(self._metrics_buffer) > self._max_buffer_size:
            self._metrics_buffer.pop(0)

    async def get_metrics_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取指标摘要

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            指标摘要
        """
        try:
            if not start_time:
                start_time = datetime.utcnow() - timedelta(hours=24)
            if not end_time:
                end_time = datetime.utcnow()

            # 过滤时间范围内的指标
            filtered_metrics = [
                m for m in self._metrics_buffer
                if start_time <= m.timestamp <= end_time
            ]

            # 按类型分组统计
            query_metrics = [m for m in filtered_metrics if m.name == "rag_query"]
            error_metrics = [m for m in filtered_metrics if m.name == "error_occurred"]
            system_metrics = [m for m in filtered_metrics if m.name.startswith("system_")]

            summary = {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "queries": {
                    "total": len(query_metrics),
                    "avg_duration": sum(m.value for m in query_metrics) / len(query_metrics) if query_metrics else 0,
                    "by_mode": self._group_by_label(query_metrics, "mode"),
                    "by_status": self._group_by_label(query_metrics, "status")
                },
                "errors": {
                    "total": len(error_metrics),
                    "by_type": self._group_by_label(error_metrics, "error_type"),
                    "by_component": self._group_by_label(error_metrics, "component")
                },
                "system": await self.collect_system_metrics()
            }

            return summary

        except Exception as e:
            logger.error("获取指标摘要失败", error=str(e))
            return {}

    def _group_by_label(
        self,
        metrics: List[MetricPoint],
        label_key: str
    ) -> Dict[str, int]:
        """
        按标签分组统计

        Args:
            metrics: 指标列表
            label_key: 标签键

        Returns:
            分组统计结果
        """
        groups = {}
        for metric in metrics:
            label_value = metric.labels.get(label_key, "unknown")
            groups[label_value] = groups.get(label_value, 0) + 1
        return groups

    def export_prometheus_metrics(self) -> str:
        """
        导出Prometheus格式指标

        Returns:
            Prometheus格式的指标文本
        """
        try:
            return generate_latest(self.registry).decode('utf-8')
        except Exception as e:
            logger.error("导出Prometheus指标失败", error=str(e))
            return ""

    async def cleanup_old_metrics(self, days: int = 7) -> None:
        """
        清理旧的指标数据

        Args:
            days: 保留天数
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)

            original_count = len(self._metrics_buffer)
            self._metrics_buffer = [
                m for m in self._metrics_buffer
                if m.timestamp > cutoff_time
            ]

            cleaned_count = original_count - len(self._metrics_buffer)

            logger.info(
                "指标清理完成",
                cleaned_count=cleaned_count,
                remaining_count=len(self._metrics_buffer),
                cutoff_days=days
            )

        except Exception as e:
            logger.error("清理指标失败", error=str(e))

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态
        """
        try:
            # 检查指标收集是否正常
            system_metrics = await self.collect_system_metrics()

            return {
                "status": "healthy" if system_metrics else "unhealthy",
                "metrics_buffer_size": len(self._metrics_buffer),
                "last_system_metrics": bool(system_metrics),
                "prometheus_enabled": self.config.monitoring.prometheus_enabled
            }

        except Exception as e:
            logger.error("指标收集器健康检查失败", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# 全局指标收集器实例
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    获取全局指标收集器实例

    Returns:
        指标收集器实例
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# 装饰器：自动记录函数执行时间
def track_execution_time(metric_name: str, labels: Dict[str, str] = None):
    """
    装饰器：追踪函数执行时间

    Args:
        metric_name: 指标名称
        labels: 标签
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                metrics = get_metrics_collector()
                metrics._add_metric_point(
                    MetricPoint(
                        name=metric_name,
                        value=duration,
                        timestamp=datetime.utcnow(),
                        labels=labels or {},
                        unit="seconds"
                    )
                )

                return result
            except Exception as e:
                duration = time.time() - start_time

                metrics = get_metrics_collector()
                metrics.record_error(type(e).__name__, func.__name__)

                raise

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                metrics = get_metrics_collector()
                metrics._add_metric_point(
                    MetricPoint(
                        name=metric_name,
                        value=duration,
                        timestamp=datetime.utcnow(),
                        labels=labels or {},
                        unit="seconds"
                    )
                )

                return result
            except Exception as e:
                duration = time.time() - start_time

                metrics = get_metrics_collector()
                metrics.record_error(type(e).__name__, func.__name__)

                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator