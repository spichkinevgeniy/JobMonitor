-- Отчёт по теневому прогону Jev рядом с Gemini.
--
-- Запуск на проде:
--   sudo docker exec -i job_monitor_db_prod psql -U postgres -d app_job \
--     < scripts/jev_shadow_report.sql
--
-- Gemini здесь — точка отсчёта, а не истина: отчёт меряет согласие с ним.
-- Кто прав там, где модели разошлись, видно только по текстам — они лежат
-- в колонке text как раз для таких случаев (запрос 7).

\echo '== 1. Сводка =='
select count(*)                                                  as vyzovov,
       count(*) filter (where jev_error is not null)              as oshibok_jev,
       count(*) filter (where llm_error is not null)              as oshibok_gemini,
       round(avg(jev_latency_ms))                                 as sredn_ms,
       percentile_cont(0.95) within group (order by jev_latency_ms) as p95_ms,
       round(sum(jev_cost_usd)::numeric, 4)                       as potracheno_usd,
       min(created_at)::date                                      as s,
       max(created_at)::date                                      as po
from jev_shadow_log;

\echo '== 2. Вакансия или нет: согласие при пороге 0,5 =='
select llm_is_vacancy                 as gemini_vakansiya,
       (jev_is_vacancy_p >= 0.5)      as jev_vakansiya,
       count(*)                       as shtuk
from jev_shadow_log
where jev_is_vacancy_p is not null and llm_is_vacancy is not null
group by 1, 2
order by 1, 2;

\echo '== 3. Калибровка: сколько вакансий по Gemini в каждой корзине уверенности Jev =='
select width_bucket(jev_is_vacancy_p, 0, 1.0000001, 10)          as korzina,
       round(min(jev_is_vacancy_p)::numeric, 2)                   as ot,
       round(max(jev_is_vacancy_p)::numeric, 2)                   as do_,
       count(*)                                                   as vsego,
       round(avg(case when llm_is_vacancy then 1 else 0 end)::numeric, 3) as dolya_vakansiy
from jev_shadow_log
where jev_is_vacancy_p is not null and llm_is_vacancy is not null
group by 1
order by 1;

\echo '== 4. Фильтр перед Gemini: сколько вызовов сэкономил бы и сколько вакансий потерял бы =='
select p.t                                                          as porog,
       count(*) filter (where s.jev_is_vacancy_p < p.t)             as ne_poshlo_v_gemini,
       round(100.0 * count(*) filter (where s.jev_is_vacancy_p < p.t) / count(*), 1) as proc_ekonomii,
       count(*) filter (where s.jev_is_vacancy_p < p.t and s.llm_is_vacancy) as poteryano_vakansiy
from jev_shadow_log s
cross join (values (0.02), (0.05), (0.1), (0.2), (0.3), (0.5)) as p(t)
where s.jev_is_vacancy_p is not null and s.llm_is_vacancy is not null
group by p.t
order by p.t;

\echo '== 5. Грейд: совпадение с Gemini по уверенности Jev (только там, где обе видят вакансию) =='
select case
         when jev_grade_confidence >= 0.9 then '1. от 0,9'
         when jev_grade_confidence >= 0.7 then '2. 0,7–0,9'
         else '3. ниже 0,7'
       end                                                         as uverennost,
       count(*)                                                    as vsego,
       round(100.0 * avg(case when jev_grade = llm_grade then 1 else 0 end), 1) as proc_sovpadeniy
from jev_shadow_log
where llm_is_vacancy and jev_is_vacancy_p >= 0.5
  and jev_grade is not null and llm_grade is not null
group by 1
order by 1;

\echo '== 6. Грейд: матрица расхождений =='
select llm_grade as gemini, jev_grade as jev, count(*) as shtuk
from jev_shadow_log
where llm_is_vacancy and jev_is_vacancy_p >= 0.5 and jev_grade <> llm_grade
group by 1, 2
order by 3 desc
limit 15;

\echo '== 7. Где Gemini сломался, а Jev видит вакансию — кандидаты в потерянные =='
select count(*) as shtuk
from jev_shadow_log
where llm_error is not null and jev_is_vacancy_p >= 0.5;

\echo '== 8. Тексты расхождений для чтения глазами (последние 20) =='
select created_at::timestamp(0)       as kogda,
       round(jev_is_vacancy_p::numeric, 2) as jev_p,
       llm_is_vacancy                 as gemini,
       left(regexp_replace(text, '\s+', ' ', 'g'), 220) as tekst
from jev_shadow_log
where text is not null
order by created_at desc
limit 20;
