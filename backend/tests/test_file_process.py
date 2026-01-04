


# def check_parse_status_job():
#     db = SessionLocal()
#     try:
#         docs = db.query(Document).filter(Document.status == "parsing").all()
#         rag = _get_ragflow_client()

#         for doc in docs:
#             dataset = rag.get_dataset(doc.knowledge_space.ragflow_knowledge_id)

#             # 通过 id 精确查询
#             results = dataset.list_documents(id=doc.ragflow_document_id)
#             if not results:
#                 continue

#             rag_doc = results[0]
#             run_status = rag_doc.run

#             if run_status == "DONE":
#                 update_document_status(db, document_id=doc.id, status="parsed")

#             elif run_status in ("FAIL", "CANCEL"):
#                 update_document_status(
#                     db,
#                     document_id=doc.id,
#                     status="failed",
#                     error_message=rag_doc.progress_msg,
#                 )

#             elif run_status == "RUNNING":
#                 # 保持 parsing，不用更新
#                 pass

#     finally:
#         db.close()
